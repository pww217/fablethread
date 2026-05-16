# engine/ — turn pipeline

## Package structure

| File | Responsibility |
|---|---|
| `ccya/engine/__init__.py` | Re-exports: `EngineConfig`, `run_turn`, `run_turn_retry`, `warmup`, `generate_seed`, `generate_pack`, `format_change_lines`, `maybe_compact`, `is_turn_in_progress`. Internal helpers for tests: `_build_jinja_env`, `_narrate_messages`, `_extract_scene_messages`, `_extract_state_messages`, `_extract_progress_messages`, `_quest_threshold_directive`, `_scene_npc_roster`, `_rules_messages`, `_expire_scene_pressures`, `_validate`. LLM client re-exports: `llm_chat`, `llm_chat_stream` |
| `ccya/engine/config.py` | `EngineConfig` dataclass, `_EventLock`, `is_turn_in_progress`, `_build_jinja_env()`, `_render()`, `_find_json()`, `_log_llm_io()`, `_log_prompts()` |
| `ccya/engine/turn.py` | `run_turn()` async orchestrator (thin — imports from submodules), `_validate()`, `run_turn_retry()`, `warmup()` |
| `ccya/engine/narrate.py` | `_narrate_messages()`, `_known_characters_for_extract()` |
| `ccya/engine/pack_gen.py` | `generate_pack()` — takes `WorldBrief`, generates `ScenarioBrief` via LLM, writes pack files to `packs/custom/<slug>/`, returns `Pack`. Uses `generate_pack_system.j2` + `generate_pack_user.j2` prompts. |
| `ccya/engine/names.py` | `generate_name_pool()`, `generate_npc_names()`, `generate_npc_names_split()`, `_build_weighted_fakers()`, `_pick()`, `_ensure_ascii()` |
| `ccya/engine/rules.py` | `_rules_messages()`, `_call_rules()`, `_avg_rules_ms()`, `_log_rules_outcome()` |
| `ccya/engine/extraction.py` | `_run_extraction_pipeline()`, all `_extract_*_messages()`, `_call_stream()`, `_context_meta()`, `_scene_npc_roster()`, `_avg_narrate_ms()`, `_avg_extract_ms()`, `_check_npc_ghost_cycle()` — all three streams (scene, state, progress) always run |
| `ccya/engine/seed.py` | `generate_seed()`, `_build_generate_seed_messages()`, `_soft_validate_seed()` |
| `ccya/engine/changes.py` | `summarize_changes()`, `format_change_lines()`, `_summarize_applied()` — `summarize_changes` includes momentum diff when `pre.pc.momentum != post.pc.momentum`; `format_change_lines` renders `⚡ Momentum {before:+d} → {after:+d}`
| `ccya/engine/pressure.py` | `_expire_scene_pressures()`, `_purge_scene_pressures()` |
| `ccya/engine/compactor.py` | `maybe_compact()`, `_extract_turns_for_compact()`, `_build_compact_messages()`, `_parse_compact_response()`, `_write_compacted_block()` |
| `ccya/engine/arc.py` | `tick_arc()`, `update_stances()`, `_salience_score()`, `_tag_overlap()` — campaign arc director: processes thread signals, manages thread lifecycle (latent→active→complete/failed/expired), handles candidate_opportunity from extraction, momentum bias for salience scoring |
| `ccya/engine/generate_pack.py` | `generate_pack_from_brief(inputs, packs_root, llm_host, llm_model, template_dir, trace_id) -> AsyncIterator[dict]` — SSE-driven ephemeral pack generation from world brief; writes `scenario.yaml` + `pack.yaml` to `packs/generated/<uuid>/`; yields `phase`, `pack_ready`, `generation_error` events |

## Public APIs

- **`run_turn(save_dir, user_input, config, template_dir, pack_style, pack_name_locales, pack_narrator_rules, pack_world_rules, pack_factions, pack_locations)`** — Async generator yielding `("token", str)`, `("phase", dict)`, `("complete", TurnResult)`. The 5-call turn pipeline.
- **`generate_seed(pack, config, overrides, template_dir)`** — LLM-generated SeedEnvelope for dynamic packs.
- **`generate_pack(brief, config, packs_dir, template_dir, max_retries)`** — LLM-generated ScenarioBrief from WorldBrief, writes pack to `packs/custom/<slug>/`, returns loaded Pack.
- **`generate_pack_from_brief(inputs, packs_root, llm_host, llm_model, template_dir, trace_id)`** — Async generator yielding SSE events (`phase`, `pack_ready`, `generation_error`); writes ephemeral pack to `packs/generated/<uuid>/`.
- **`warmup(config)`** — Silent chat call to pre-load model.
- **`is_turn_in_progress(save_dir)`** — Guard against concurrent turns.
- **`EngineConfig`** dataclass — all tunable params (temps, timeouts, token budget, thinking toggles, compaction settings).
- **`format_change_lines(changes)`** → emoji display lines

## 5-call turn pipeline (run_turn)

1. **Rules / Intent** (Call 0, `llm_chat`, non-streaming) — classifies intent, resolves dice via `rules.resolve_check()`, returns `IntentEnvelope` + `RulesOutcome` (band, directive, dice).
2. **Narrate** (Call 1, streaming → SSE → `chronicle.md`) — prose narrative.
3. **Scene Extract** (Call 2a, `llm_chat`, JSON → `SceneExtractResult`) — scene tags, location change, location description, present NPCs, compendium NPC updates. Always runs.
4. **State Extract** (Call 2b, `llm_chat`, JSON → `StateExtractResult`) — inventory deltas, condition add/remove. Always runs.
5. **Progress Extract** (Call 2c, `llm_chat`, JSON → `ProgressExtractResult`) — quest updates, recent events, actions, outcome_summary, gm_beat, beat_disposition, scene_pressure add/remove/update. Always runs.

Steps 2a–2c merge into `StateDelta` → `_validate()` → `apply_delta()` → `summarize_changes()` → persist (atomic writes: `events.jsonl`, `state.yaml`, `chronicle.md`).

After persist, `maybe_compact()` runs if `turn % compact_every == 0`.

## Internal functions

### turn.py
- `_compute_ages(state)` → `dict[str, int]` — scene_age, location_age, combat_age
- `_compute_quest_ages(state, current_turn)` → `list[dict]` — stalled quest info
- `_compute_threat_ages(state)` → `list[dict]` — threat age for imperative directives (id, text, urgency, age), sorted oldest-first, excludes pressures with turn_added=0
- `_check_floor_relief(state, config, band)` → `None` — checks momentum floor and injects `breathing_room` beat when relief conditions met; tracks consecutive floor turns via `state["meta"]["consecutive_floor_count"]`
- Condition age pass (inline in `run_turn` and `run_turn_retry`) — decrements `turns_remaining` on all active conditions, removes expired ones (≤0), logs `condition_expired` event via `append_event`. Runs after delta application and pressure aging. Permanent conditions (`turns_remaining=None`) are skipped. New conditions without explicit `turns_remaining` get a default TTL of 10 turns (set in `apply_delta`).
- `run_turn(save_dir, user_input, config=None, *, template_dir=None, pack_style="", pack_name_locales=[], pack_narrator_rules=[], pack_world_rules=[], pack_factions=[], pack_locations=[])` → `AsyncIterator[tuple[str, Any]]` — 5-call turn pipeline (rules→narrate→scene→state→progress extract). Detects avoidance intent from player input; passes to pressure pipeline for decay. Yields ("phase", dict), ("token", str), ("complete", TurnResult).
- `_validate(state, delta)` → `list[dict]` — validates inventory_remove IDs exist, rejects zero-balance removes, warns on overdraw
- `_strip_fallback(narration, *, trace_id, turn)` → `str` — strips fallback sentinel lines (`*That action didn't resolve as expected...`) from narration before chronicle persistence and extraction
- `_check_npc_ghost_cycle(scene_result, state, *, trace_id, turn_no)` → `SceneExtractResult` — detects same-turn npc_remove+add cycles, drops both ops, logs warning
- `run_turn_retry(save_dir, rules_outcome, intent, config=None, *, template_dir=None, pack_style="", pack_name_locales=[], pack_narrator_rules=[], pack_world_rules=[], pack_factions=[], pack_locations=[])` → `AsyncIterator[tuple[str, Any]]` — skips Call 0, re-runs narrate + extraction with same rules outcome; computes `threat_ages` and passes all narrator threat-directive arguments (`threat_ages`, `turn_no`, `threat_pressure_at`, `threat_imperative_at`, `building_threat_imperative_at`) matching `run_turn`
- `warmup(config)` → `None` (async) — silent chat call to pre-load model

### config.py
- `EngineConfig` dataclass — all tunable params (temps, timeouts, token budget, thinking toggles, compaction settings, scene pressure TTL/escalation thresholds, avoidance keywords/decay, momentum floor/relief thresholds)
- `_EventLock` class — async lock preventing concurrent turns per save_dir
- `is_turn_in_progress(save_dir)` → `bool` — guard against concurrent turns
- `_build_jinja_env(template_dir)` → `Environment` — Jinja2 env with autoescape
- `_render(env, template, ctx)` → `str` — renders Jinja template with context
- `_find_json(text)` → `dict | None` — extracts JSON object from LLM text response
- `_truncate(s, n)` → `str` — truncates string to n chars
- `_log_llm_io(trace_id, phase, messages=None, response=None, extra=None, max_chars=2000)` — logs LLM I/O for debugging
- `_log_prompts(turn, phase, messages)` — logs rendered prompts when config.log_prompts is True

### narrate.py
- `_narrate_messages(env, state, user_input, *, chronicle_tail="", recent_turns=None, enable_narrate_thinking=False, pack_style="", narrator_rules=[], world_rules=[], rules_outcome=None, npc_name_pool=None, recently_left=None, momentum=0, pending_gm_beat=None, deescalate=False, ages=None, known_npcs=None, present_npcs=None, compendium_bios=None, pc_allegiance=None, scene_pressure=None, turn_no=0, world_factions=[], world_locations=[], threat_ages=None, threat_pressure_at=3, threat_imperative_at=5, building_threat_imperative_at=4)` → `list[dict]` — prompt builder for narrator; builds `current_arc_ctx` dict (visible_goal, thematic_question, phase, active_threads, pc_drive) from state.arc and passes to system prompt; accepts momentum, pending_gm_beat, deescalate, ages, known_npcs, present_npcs, compendium_bios, narrator_rules, world_rules, scene_pressure, world faction/location context, and threat age data with imperative thresholds
- `_known_characters_for_extract(state, compact=True)` → `list[dict]` — deduped NPC roster from compendium

### rules.py (engine/rules.py — NOT ccya/rules.py)
- `_rules_messages(env, state, user_input, recent_turns=None, turn_no=0, present_npcs=None, last_outcome=None)` → `list[dict]` — prompt builder for rules/intent call; `last_outcome` is an optional string sourced from the previous turn's `outcome_summary`, used to replace the full last-turn narrative with a concise outcome
- `_call_rules(messages, config, trace_id)` → `tuple[IntentEnvelope, dict, str]` (async) — LLM call wrapper with retry on parse failure; calls `apply_thinking(messages, False)` to suppress thinking tokens unconditionally
- `_avg_rules_ms(save_dir, n=5)` → `int` — rolling average rules latency from events
- `_log_rules_outcome(turn, intent, outcome)` — logs rules outcome for debugging
- Near-miss directive logic lives in `ccya/rules.py:build_directive()` — when `band == "fail"` and `final_total >= 6`, the directive appends a near-miss complication note giving the narrator latitude to make failures narratively generative rather than fully punitive.

### names.py
- `generate_name_pool(locales, *, pc_count=3, npc_count=8, location_count=5, seed=None)` → `dict[str, list[str]]` — culturally-appropriate name pools via Faker (pc, npc, location keys)
- `generate_npc_names(locales, *, count=10, seed=None)` → `list[str]` — flat list of NPC name candidates
- `generate_npc_names_split(locales, *, male_count=5, female_count=5, seed=None)` → `dict[str, list[str]]` — gender-split name pool for gender-aware casting
- `_build_weighted_fakers(locales, rng, seed)` → `tuple[list[Faker], list[float]]` — weighted Faker instances
- `_pick(fakers, weights, rng)` → `Faker` — weighted random selection
- `_ensure_ascii(name)` → `str` — strips non-ASCII characters

### extraction.py
- `_run_extraction_pipeline(env, state, narration, *, rules_outcome=None, intent=None, config, trace_id, turn_no, deescalate=0.0, quest_ages=None, recent_turns=None)` → `tuple[StateDelta, list[str], str, dict, ProgressExtractResult, SceneExtractResult]` (async) — runs 3 streams in sequence (scene, state, progress — all always run), dedup pre-pass redirects compendium NPC IDs and npc_add entries before StateDelta merge, update-only guard drops `scene_pressure_update` entries whose id is not in existing state pressures, merges into StateDelta; returns 6-tuple including scene_result; `deescalate` is float (0.0–1.0). After state stream, `_build_extraction_context` computes `_ExtractionContext` from scene + state results, threaded into progress stream.
- `_ExtractionContext` dataclass — carries this-turn deltas from scene + state streams into progress stream; fields: `present_npcs_this_turn`, `location_this_turn`, `scene_tags_this_turn`, `scene_pressure_this_turn`, `inventory_this_turn`, `conditions_this_turn`
- `_build_extraction_context(state, scene_result, state_result)` → `_ExtractionContext` — pure function that applies scene/state deltas in-memory to compute this-turn derived context; does NOT mutate `state`
- `_extract_scene_messages(env, narration, state, *, rules_outcome=None, enable_thinking=False, recent_turns=None)` → `list[dict]` — prompt builder for scene extractor (scoped to NPC presence, location change, scene tags/tagline, location_description only); no longer receives scene_pressure, deescalate, quest_ages, or active_quests context
- `_extract_state_messages(env, narration, state, *, scene_result, rules_outcome=None, enable_thinking=False)` → `list[dict]` — prompt builder for state extractor
- `_extract_progress_messages(env, narration, state, *, state_result, extraction_ctx, enable_thinking=False, intent=None, deescalate=0.0, quest_ages=[], recent_turns=None, turn_no=0)` → `list[dict]` — prompt builder for progress extractor; receives `extraction_ctx: _ExtractionContext` (this-turn derived NPC/inventory/location/pressure/conditions), intent, recent_turns, turn_no, deescalate magnitude, quest_ages; `deescalate` is float; active_threads dict includes `tags` field (list[str]) for LLM signal matching
- Post-processing in `_run_extraction_pipeline`: after progress extraction, `recent_events_add.turn` is overwritten engine-side with `turn_no` on every `RecentEvent` (authoritative stamp, belt-and-suspenders over prompt instruction)
- `_call_stream(messages, config, trace_id, phase, model_cls, strip_keys=("_reasoning",))` → `tuple[result, usage, attempts, retry_errors]` (async) — LLM call with retry
- `_parse_stream_result(raw, model_cls, strip_keys=("_reasoning",))` → model instance — JSON parsing + model validation for streams
- `_context_meta(rendered_system, rendered_user, was_trimmed, trimmed_chars)` → `dict` — computes context size signals for telemetry
- `_dedup_compendium_add(proposed, existing_npcs)` → `CompendiumNpcUpdate` — redirects proposed NPC ID to existing NPC ID if name/alias matches (engine-level dedup safety net)
- `_scene_npc_roster(known_characters)` → `list[dict]` — deduped NPC roster for scene extractor
- `_quest_threshold_directive(active_quests)` → `str` — guidance on when to start new quests
- `_avg_narrate_ms(save_dir, n=5)` → `int` — rolling average narrate latency from events
- `_avg_extract_ms(save_dir, n=5)` → `int` — rolling average extract latency from events

### seed.py
- `generate_seed(pack, config, *, overrides=None, seed=None, template_dir=None)` → `SeedEnvelope` (async) — LLM-generated SeedEnvelope for dynamic packs. Retries on parse/validation failure (up to 1 + max_retries). Sources world_facts from scenario.world_facts (new) → manifest.baseline_facts → parse_world_facts(world.md) (legacy). Raises ValueError on static packs. Injects world_facts into world_state, runs soft validation.
- `_build_generate_seed_messages(env, pack, overrides=None)` → `list[dict]` — renders generate_seed_system.j2 + generate_seed_user.j2; passes name_seed (randomized if scenario.name_seed is 0)
- `_soft_validate_seed(envelope, pack, overrides=None)` → `list[str]` — word count, cliché, player-dependent checks

### pack_gen.py
- `generate_pack(brief, config, packs_dir, *, template_dir=None, max_retries=2)` → `Pack` (async) — takes `WorldBrief`, generates `ScenarioBrief` via LLM, writes `pack.yaml` + `scenario.yaml` to `packs/custom/<slug>/`, returns loaded `Pack`. Uses `generate_pack_system.j2` + `generate_pack_user.j2` prompts. Retries on parse/validation failure.
- `_slugify(text)` → `str` — converts concept string to URL-safe slug (max 40 chars)
- `_build_generate_pack_messages(env, brief, name_pool, name_seed)` → `list[dict]` — renders pack generation prompts

### generate_pack.py
- `generate_pack_from_brief(inputs, packs_root, llm_host, llm_model, template_dir, trace_id) -> AsyncIterator[dict]` (async) — SSE-driven ephemeral pack generation from world brief; renders `generate_pack_system.j2` + `generate_pack_user.j2`, calls `llm_chat`, parses YAML into `ScenarioBrief`, writes `scenario.yaml` + `pack.yaml` to `packs/generated/<uuid>/`; yields `{"type":"phase","label":...}`, `{"type":"pack_ready","pack_id":...}`, or `{"type":"generation_error","error":...}`
- `_convert_tuples_to_lists(obj)` → `Any` — recursively converts tuples to lists for YAML compatibility (yaml.dump serializes tuples with !!python/tuple which safe_load can't read)

### changes.py
- `summarize_changes(pre, post, applied, rejected)` → `dict` — diffs pre vs post state → `{inventory, player, facts, quests}`
- `format_change_lines(changes)` → `list[str]` — emoji display lines for UI
- `_summarize_applied(applied)` → `list[str]` — internal diff line formatter

### pressure.py
- `_expire_scene_pressures(state, delta, config=None, avoidance=False)` — post-extraction expiry/urgency escalation for `scene_pressure`. Removes pressures past `max_turns`, applies default 4-turn TTL cap for background/building pressures (escalates to immediate instead of removing, giving extractor one more turn to react), then applies configurable escalation thresholds (background→building at 6, building→immediate at 10). Immediate pressures get a TTL stamp (`turn_became_immediate` + `max_turns`) on escalation; TTL defaults to 8 turns from escalation turn. When `avoidance=True`, non-immediate pressures get extra age increment (configurable via `avoidance_decay_per_turn`), simulating time passing while player creates distance. Write-back guarantee: mutations to state dict items (urgency, turn_became_immediate, max_turns) survive to persisted state; removed IDs are appended to `delta.scene_pressure_remove` which `apply_delta` uses to filter state.
- `_purge_scene_pressures(state, delta, *, location_changed=False, combat_ended=False, config=None)` — removes stale/irrelevant pressures. On location change: only auto-purges `urgency == "background"` pressures; `immediate` and `building` pressures survive location change and must be explicitly removed by the scene extractor. On combat end: removes `immediate` pressures. Age cap at 15 turns default.
- `_check_floor_relief(state, config, band)` — checks momentum floor and injects `breathing_room` GM beat when momentum has been at floor (`config.momentum_floor`, default -3) for `config.momentum_floor_relief_turns` (default 2) consecutive turns without a success/crit_success band. Tracks consecutive floor count via `state["meta"]["consecutive_floor_count"]`. Does not overwrite existing `pending_gm_beat`.

### compactor.py
- `maybe_compact(save_dir, state, config)` → `tuple[state, bool]` (async) — runs compaction if `turn % compact_every == 0`. Returns `(state, compaction_ran)` where `compaction_ran` is True only when compaction actually produced bullets or sanitization. Mutates chronicle.md and state. Compacts prior_history bullets, applies state sanitization (NPC merge, inventory remove, quest close, pressure remove, condition remove), and consolidates recent_events via LLM. Emits a `"kind": "compaction"` event record to `events.jsonl` when compaction runs. Phase signals (`compact_start`, `compact_done`) are emitted by the caller only when `compaction_ran` is True.
- `_extract_turns_for_compact(save_dir, start_turn, end_turn)` → `list[dict]` — reads chronicle.md for turns in range, returns {turn, input, narrative}
- `_build_compact_messages(env, state, turns)` → `list[dict]` — renders compact_system.j2 + compact_user.j2; passes recent_events from state.scene.recent_events to template
- `_parse_compact_response(response_text)` → `tuple[str, CompactorSanitizationResult | None]` — extracts bullet lines (matching `- [T\d+] `) + JSON sanitization from LLM output (last JSON object, validated through CompactorSanitizationResult)
- `_write_compacted_block(save_dir, bullets_text, compact_start, compact_end)` — writes COMPACTED block to chronicle.md (prepends if none exists, appends after existing block), then removes prose sections for turns in [compact_start, compact_end]
- `_apply_sanitization(state, san)` — applies CompactorSanitizationResult to state in-place; validates all IDs against allowlists; unknown IDs silently skipped; logs structured event with `quests_closed`, `inventory_removed`, `npcs_merged`, `pressures_removed`, `conditions_removed`
- `_sanitization_nonempty(san)` → `bool` — returns True when any of the five sanitization lists (npc_merge, inventory_remove, quest_close, pressure_remove, condition_remove) is non-empty

### arc.py
- `tick_arc(arc, drift=None, drift_analysis=None)` → `CampaignArc` — scores arc engagement based on drift overlap with active thread tags. Accepts structured `drift_analysis` (list[DriftAnalysis]) with per-thread match/no-match, falls back to legacy `drift` (list[str]) substring matching. Thread lifecycle (signals, completion, promotion, latent hygiene) is handled by `_apply_thread_signals` / `_candidate_to_latent_thread` in engine/turn.py. This function only updates arc_engagement.
- `update_stances(stances, user_input)` → `dict` — updates expressed stances based on player input keywords (compassionate/ruthless/defiant/cautious).
- `_tag_overlap(a, b)` → `int` — count of tags present in both lists.

## Character creation

- **`POST /new-game`**: static packs load `pack.seed` with hard overrides; dynamic packs call `generate_seed()`.
- **Generate Seed** (dynamic packs only): LLM generates `SeedEnvelope` (full `GameState` + opening narrative + actions) from pack manifest + optional `PlayerOverrides`.

## Extraction pipeline conventions

- **Cross-stream dependencies are minimal by design.**
  - Scene → State passes `location_change` (id, name, description) + `present_npcs` (id, name, title, notes, bio).
  - State → Progress passes minimal surface: `items_gained` (item **names** from `inventory_add`) + `items_lost` (item **ids** from `inventory_remove`).
  - No full state re-sends between extractors.
- **Field routing** (post-remediation):
  - `SceneExtractResult`: scene_tags, scene_tagline, location_change, location_description, npc_add/remove/update, **compendium_npc_update**. (No pressure fields — all pressure lifecycle migrated to progress extractor.)
  - `StateExtractResult`: inventory_add/remove/update, pc_condition_add/remove. (No `failed` — removed from LLM output.)
  - `ProgressExtractResult`: quest_updates, recent_events_add/update/remove, **actions**, **outcome_summary**, **scene_pressure_add/remove/update** (all three pressure lifecycle ops), **gm_beat**, **beat_disposition**.
- **Conditions are structured.** `pc.conditions` is `list[Condition]` (`id`, `label`, `description`, `added_turn`). `apply_delta` stamps `added_turn` and uses `id`-based dedup — no text normalization. String coercion exists for test convenience only; LLM output must use the full object.
- **`events.jsonl`** gains an `extraction` key with per-stream `{rendered_system, rendered_user, output, tokens_in, tokens_out, ms, skipped}` for debugging.
- **Delta flow**: three extract results → `StateDelta` → `_validate()` (checks e.g. `inventory_remove` IDs exist, returns `rejections`) → `apply_delta()` (mutates state in-place) → `summarize_changes()` (diffs pre vs post → `changes{inventory, player, facts, quests}`).
