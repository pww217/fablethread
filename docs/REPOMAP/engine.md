# engine/ — turn pipeline

## Package structure

| File | Responsibility |
|---|---|
| `ccya/engine/__init__.py` | Re-exports: `EngineConfig`, `run_turn`, `run_turn_retry`, `warmup`, `generate_seed`, `format_change_lines`, `maybe_compact`, `is_turn_in_progress`. Internal helpers for tests: `_build_jinja_env`, `_narrate_messages`, `_extract_scene_messages`, `_extract_state_messages`, `_extract_progress_messages`, `_quest_threshold_directive`, `_scene_npc_roster`, `_rules_messages`, `_expire_scene_pressures`, `_validate`. LLM client re-exports: `llm_chat`, `llm_chat_stream` |
| `ccya/engine/config.py` | `EngineConfig` dataclass, `_EventLock`, `is_turn_in_progress`, `_build_jinja_env()`, `_render()`, `_find_json()`, `_log_llm_io()`, `_log_prompts()` |
| `ccya/engine/turn.py` | `run_turn()` async orchestrator (thin — imports from submodules), `_validate()`, `run_turn_retry()`, `warmup()` |
| `ccya/engine/narrate.py` | `_narrate_messages()`, `_known_characters_for_extract()`, `build_state_slice()` |
| `ccya/engine/names.py` | `generate_name_pool()`, `generate_npc_names()`, `generate_npc_names_split()`, `generate_faction_pool()`, `generate_location_pool()`, `_slugify()` |
| `ccya/engine/rules.py` | `_rules_messages()`, `_call_rules()`, `_avg_rules_ms()`, `_log_rules_outcome()` |
| `ccya/engine/extraction.py` | `_run_extraction_pipeline()`, all `_extract_*_messages()`, `_call_stream()`, `_context_meta()`, `_scene_npc_roster()`, `_avg_narrate_ms()`, `_avg_extract_ms()` |
| `ccya/engine/seed.py` | `generate_seed()`, `_build_generate_seed_messages()`, `_soft_validate_seed()` |
| `ccya/engine/changes.py` | `summarize_changes()`, `format_change_lines()`, `_summarize_applied()` |
| `ccya/engine/pressure.py` | `_expire_scene_pressures()`, `_purge_scene_pressures()` |
| `ccya/engine/compactor.py` | `maybe_compact()`, `_extract_turns_for_compact()`, `_build_compact_messages()`, `_parse_compact_response()`, `_write_compacted_block()` |

## Public APIs

- **`run_turn(save_dir, user_input, config, template_dir, pack_style, pack_examples, pack_name_locales)`** — Async generator yielding `("token", str)`, `("phase", dict)`, `("complete", TurnResult)`. The 5-call turn pipeline.
- **`generate_seed(pack, config, overrides, template_dir)`** — LLM-generated SeedEnvelope for dynamic packs.
- **`warmup(config)`** — Silent chat call to pre-load model.
- **`is_turn_in_progress(save_dir)`** — Guard against concurrent turns.
- **`EngineConfig`** dataclass — all tunable params (temps, timeouts, token budget, thinking toggles, compaction settings).
- **`format_change_lines(changes)`** → emoji display lines

## 5-call turn pipeline (run_turn)

1. **Rules / Intent** (Call 0, `llm_chat`, non-streaming) — classifies intent, resolves dice via `rules.resolve_check()`, returns `IntentEnvelope` + `RulesOutcome` (band, directive, dice).
2. **Narrate** (Call 1, streaming → SSE → `chronicle.md`) — prose narrative. Emits `<scope>{"active_domains":["..."]}</scope>` as the last line. Server-side stream filter strips the tail before SSE emission. `RulesOutcome` injected as BINDING block the narrator must not contradict.
3. **Scope parsing** — `_split_scope_tail()` extracts `active_domains` from the narrator's scope tail. Falls back to `_DEFAULT_DOMAINS` (all 7) on missing/malformed tag.
4. **Scene Extract** (Call 2a, `llm_chat`, JSON → `SceneExtractResult`) — scene tags, location change, present NPCs, actions, outcome summary. Skipped when neither `scene` nor `location_change` is in `active_domains`.
5. **State Extract** (Call 2b, `llm_chat`, JSON → `StateExtractResult`) — inventory deltas, condition add/remove, failed preconditions. Skipped when neither `inventory` nor `pc_condition` is in `active_domains`.
6. **Progress Extract** (Call 2c, `llm_chat`, JSON → `ProgressExtractResult`) — quest updates, recent events, compendium NPC updates. Always runs (post-narration storytelling brain).

Steps 2a–2c merge into `StateDelta` → `_validate()` → `apply_delta()` → `summarize_changes()` → persist (atomic writes: `events.jsonl`, `state.yaml`, `chronicle.md`).

After persist, `maybe_compact()` runs if `turn % compact_every == 0`.

## Internal functions

### turn.py
- `_compute_ages(state)` → `dict[str, int]` — scene_age, location_age, combat_age
- `_compute_quest_ages(state, current_turn)` → `list[dict]` — stalled quest info
- `_ALL_DOMAINS` — frozenset of 7 valid domain names
- `_DEFAULT_DOMAINS` — list of all 7 domains (fallback when no scope tag)
- `_SCOPE_OPEN`, `_SCOPE_CLOSE`, `_SCOPE_TAIL_RE`, `_SCOPE_TAIL_BUFFER_SIZE` — constants for scope tail parsing
- `_split_scope_tail(text)` → `tuple[str, list[str] | None]` — extracts `<scope>...</scope>` JSON tail, returns (prose, active_domains | None)
- `_StreamTailFilter` — filters streaming text to suppress everything from `<scope>` onward; maintains sliding tail buffer for cross-chunk sentinel detection
- `run_turn(save_dir, user_input, config=None, *, template_dir=None, pack_style="", pack_examples=None, pack_name_locales=[])` → `AsyncIterator[tuple[str, Any]]` — 5-call turn pipeline (rules→narrate→scope-parse→scene→state→progress extract). Yields ("phase", dict), ("token", str), ("complete", TurnResult).
- `_validate(state, delta)` → `list[dict]` — validates inventory_remove IDs exist, warns on overdraw
- `run_turn_retry(save_dir, rules_outcome, intent, config=None, *, template_dir=None, pack_style="", pack_examples=None, pack_name_locales=[])` → `AsyncIterator[tuple[str, Any]]` — skips Call 0, re-runs narrate + extraction with same rules outcome
- `warmup(config)` → `None` (async) — silent chat call to pre-load model

### config.py
- `EngineConfig` dataclass — all tunable params (temps, timeouts, token budget, thinking toggles, compaction settings)
- `_EventLock` class — async lock preventing concurrent turns per save_dir
- `is_turn_in_progress(save_dir)` → `bool` — guard against concurrent turns
- `_build_jinja_env(template_dir)` → `Environment` — Jinja2 env with autoescape
- `_render(env, template, ctx)` → `str` — renders Jinja template with context
- `_find_json(text)` → `dict | None` — extracts JSON object from LLM text response
- `_truncate(s, n)` → `str` — truncates string to n chars
- `_log_llm_io(trace_id, phase, messages=None, response=None, extra=None, max_chars=2000)` — logs LLM I/O for debugging
- `_log_prompts(turn, phase, messages)` — logs rendered prompts when config.log_prompts is True

### narrate.py
- `_narrate_messages(env, state, user_input, *, chronicle_tail="", recent_turns=None, enable_narrate_thinking=False, pack_style="", rules_outcome=None, npc_name_pool=None, last_turn_failed=None, recently_left=None, momentum=0, pending_gm_beat=None, deescalate=False, ages=None, known_npcs=None, present_npcs=None, world_factions=None, world_locations=None, pc_allegiance=None)` → `list[dict]` — prompt builder for narrator; accepts momentum, pending_gm_beat, deescalate, ages, known_npcs, present_npcs, world context params
- `_known_characters_for_extract(state, compact=True)` → `list[dict]` — deduped NPC roster from compendium
- `build_state_slice(state)` — (used in prompts for state context)

### rules.py (engine/rules.py — NOT ccya/rules.py)
- `_rules_messages(env, state, user_input, recent_turns=None)` → `list[dict]` — prompt builder for rules/intent call
- `_call_rules(messages, config, trace_id)` → `tuple[IntentEnvelope, dict, str]` (async) — LLM call wrapper with retry on parse failure
- `_avg_rules_ms(save_dir, n=5)` → `int` — rolling average rules latency from events
- `_log_rules_outcome(turn, intent, outcome)` — logs rules outcome for debugging

### names.py
- `generate_name_pool(locales, *, pc_count=3, npc_count=8, location_count=5, seed=None)` → `dict[str, list[str]]` — culturally-appropriate name pools via Faker (pc, npc, location keys)
- `generate_npc_names(locales, *, count=10, seed=None)` → `list[str]` — flat list of NPC name candidates
- `generate_npc_names_split(locales, *, male_count=5, female_count=5, seed=None)` → `dict[str, list[str]]` — gender-split name pool for gender-aware casting
- `generate_faction_pool(seed=None, count=4)` → `list[dict[str, str]]` — deterministic faction name generation (id, name, alignment)
- `generate_location_pool(seed=None, count=5)` → `list[dict[str, str]]` — deterministic location name generation (id, name)
- `_slugify(value)` → `str` — URL-safe slug conversion
- `_build_weighted_fakers(locales, rng, seed)` → `tuple[list[Faker], list[float]]` — weighted Faker instances
- `_pick(fakers, weights, rng)` → `Faker` — weighted random selection

### extraction.py
- `_run_extraction_pipeline(env, state, narration, *, active_domains, rules_outcome=None, intent=None, config, trace_id, turn_no, pack_examples=None, deescalate=False, quest_ages=None)` → `tuple[StateDelta, list[str], str, list[str], dict, ProgressExtractResult]` (async) — runs 3 streams in sequence (scene gated by active_domains, state gated by active_domains, progress always runs), merges into StateDelta
- `_extract_scene_messages(env, narration, state, *, active_domains, rules_outcome=None, enable_thinking=False)` → `list[dict]` — prompt builder for scene extractor
- `_extract_state_messages(env, narration, state, *, active_domains, scene_result, rules_outcome=None, enable_thinking=False, pack_examples=None)` → `list[dict]` — prompt builder for state extractor
- `_extract_progress_messages(env, narration, state, *, active_domains, scene_result, state_result, rules_outcome=None, enable_thinking=False, deescalate=False, quest_ages=None)` → `list[dict]` — prompt builder for progress extractor
- `_call_stream(messages, config, trace_id, phase, model_cls, strip_keys=("_reasoning",))` → `tuple[result, usage, attempts, retry_errors]` (async) — LLM call with retry
- `_parse_stream_result(raw, model_cls, strip_keys=("_reasoning",))` → model instance — JSON parsing + model validation for streams
- `_context_meta(rendered_system, rendered_user, was_trimmed, trimmed_chars)` → `dict` — computes context size signals for telemetry
- `_scene_npc_roster(known_characters)` → `list[dict]` — deduped NPC roster for scene extractor
- `_quest_threshold_directive(active_quests)` → `str` — guidance on when to start new quests
- `_avg_narrate_ms(save_dir, n=5)` → `int` — rolling average narrate latency from events
- `_avg_extract_ms(save_dir, n=5)` → `int` — rolling average extract latency from events

### seed.py
- `generate_seed(pack, config, *, overrides=None, seed=None, template_dir=None)` → `SeedEnvelope` (async) — LLM-generated SeedEnvelope for dynamic packs. Retries on parse/validation failure (up to 1 + max_retries). Injects baseline_facts into world_state, sets faction/location pool seeds, runs soft validation.
- `_build_generate_seed_messages(env, pack, overrides=None)` → `list[dict]` — renders generate_seed_system.j2 + generate_seed_user.j2
- `_soft_validate_seed(envelope, pack, overrides=None)` → `list[str]` — word count, cliché, player-dependent checks

### changes.py
- `summarize_changes(pre, post, applied, rejected)` → `dict` — diffs pre vs post state → `{inventory, player, facts, quests}`
- `format_change_lines(changes)` → `list[str]` — emoji display lines for UI
- `_summarize_applied(applied)` → `list[str]` — internal diff line formatter

### pressure.py
- `_expire_scene_pressures(state, delta, config=None)` — post-extraction expiry/urgency escalation for `scene_pressure`. Removes pressures past `max_turns`, escalates background→building→immediate at config thresholds (default 6/10).
- `_purge_scene_pressures(state, delta, *, location_changed=False, combat_ended=False, config=None)` — removes stale/irrelevant pressures (location change, combat end, age cap at 15 turns default).

### compactor.py
- `maybe_compact(save_dir, state, config)` → `state` (async) — runs compaction if `turn % compact_every == 0`. Mutates chronicle.md and state.
- `_extract_turns_for_compact(save_dir, start_turn, end_turn)` → `list[dict]` — reads chronicle.md for turns in range, returns {turn, input, narrative}
- `_build_compact_messages(env, state, turns, events)` → `list[dict]` — renders compact_system.j2 + compact_user.j2
- `_parse_compact_response(response_text)` → `tuple[str, list[str]]` — extracts bullet lines (matching `- [T\d+] `) + JSON events from LLM output (last JSON array)
- `_write_compacted_block(save_dir, bullets_text)` — appends COMPACTED block to chronicle.md (prepends if none exists, appends after existing block)

## Character creation

- **`POST /new-game`**: static packs load `pack.seed` with hard overrides; dynamic packs call `generate_seed()`.
- **Generate Seed** (dynamic packs only): LLM generates `SeedEnvelope` (full `GameState` + opening narrative + actions) from pack manifest + optional `PlayerOverrides`.

## Extraction pipeline conventions

- **Cross-stream dependencies are minimal by design.**
  - Scene → State passes `location_change` (id, name, description) + `present_npcs` (id, name, title, notes, bio).
  - Scene → Progress passes `present_npcs` (from scene result).
  - State → Progress passes minimal surface: `items_gained` (item **names** from `inventory_add`) + `items_lost` (item **ids** from `inventory_remove`).
  - No full state re-sends between extractors.
- **Conditions are structured.** `pc.conditions` is `list[Condition]` (`id`, `label`, `description`, `added_turn`). `apply_delta` stamps `added_turn` and uses `id`-based dedup — no text normalization. String coercion exists for test convenience only; LLM output must use the full object.
- **`events.jsonl`** gains an `extraction` key with per-stream `{rendered_system, rendered_user, output, tokens_in, tokens_out, ms, skipped}` for debugging.
- **`events.jsonl`** gains a `scope` key with `{active_domains, decided_by, skipped_streams}` for telemetry.
- **Stream skipping**: scene skips when neither `scene` nor `location_change` is in `active_domains`; state skips when neither `inventory` nor `pc_condition` is in `active_domains`; progress always runs. Check `extraction_event["scene"]["skipped"]` / `extraction_event["state"]["skipped"]` in events.
- **Delta flow**: three extract results → `StateDelta` → `_validate()` (checks e.g. `inventory_remove` IDs exist, returns `rejections`) → `apply_delta()` (mutates state in-place) → `summarize_changes()` (diffs pre vs post → `changes{inventory, player, facts, quests}`).
