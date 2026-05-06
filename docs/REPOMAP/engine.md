# engine/ — turn pipeline

## Package structure

| File | Responsibility |
|---|---|
| `ccya/engine/__init__.py` | Re-exports: `EngineConfig`, `run_turn`, `generate_seed`, `warmup`, `format_change_lines` |
| `ccya/engine/config.py` | `EngineConfig` dataclass, `_EventLock`, `is_turn_in_progress`, Jinja env setup |
| `ccya/engine/turn.py` | `run_turn()` async orchestrator (thin — imports from submodules) |
| `ccya/engine/narrate.py` | `_narrate_messages()`, NPC name generation (absorbs old `names.py`) |
| `ccya/engine/rules.py` | `_rules_messages()`, `_call_rules()`, retry logic (NOT `ccya/rules.py`) |
| `ccya/engine/extraction.py` | `_run_extraction_pipeline()`, all `_extract_*_messages`, `_call_stream()` |
| `ccya/engine/seed.py` | `generate_seed()`, `_build_generate_seed_messages()`, `_soft_validate_seed()` |
| `ccya/engine/changes.py` | `summarize_changes()`, `format_change_lines()`, `_summarize_applied()` |
| `ccya/engine/pressure.py` | `_expire_scene_pressures()` |
| `ccya/engine/compactor.py` | `maybe_compact()`, chronicle compaction + recent_events pruning |

## Public APIs

- **`run_turn(save_dir, user_input, config, template_dir, pack_style, pack_examples, pack_name_locales)`** — Async generator yielding `("token", str)`, `("phase", dict)`, `("complete", TurnResult)`. The 5-call turn pipeline.
- **`generate_seed(pack, config, overrides, template_dir)`** — LLM-generated SeedEnvelope for dynamic packs.
- **`warmup(config)`** — Silent chat call to pre-load model.
- **`is_turn_in_progress(save_dir)`** — Guard against concurrent turns.
- **`EngineConfig`** dataclass — all tunable params (temps, timeouts, token budget, thinking toggles, compaction settings).
- **`format_change_lines(changes)`** → emoji display lines

## 5-call turn pipeline (run_turn)

1. **Rules / Intent** (Call 0, `llm_chat`, non-streaming) — classifies intent, resolves dice via `rules.resolve_check()`, returns `IntentEnvelope` (scope controls which extractors run) + `RulesOutcome` (band, directive, dice).
2. **Narrate** (Call 1, streaming → SSE → `chronicle.md`) — prose narrative. `RulesOutcome` injected as BINDING block the narrator must not contradict.
3. **Scene Extract** (Call 2a, `llm_chat`, JSON → `SceneExtractResult`) — scene tags, location change, present NPCs, actions, outcome summary.
4. **State Extract** (Call 2b, `llm_chat`, JSON → `StateExtractResult`) — inventory deltas, condition add/remove, failed preconditions.
5. **Progress Extract** (Call 2c, `llm_chat`, JSON → `ProgressExtractResult`) — quest updates, recent events, compendium NPC updates.

Steps 2a–2c merge into `StateDelta` → `_validate()` → `apply_delta()` → `summarize_changes()` → persist (atomic writes: `events.jsonl`, `state.yaml`, `chronicle.md`).

After persist, `maybe_compact()` runs if `turn % compact_every == 0`.

## Internal functions

### turn.py
- `run_turn()` — async orchestrator
- `run_turn_retry()` — retry wrapper for extraction failures

### config.py
- `EngineConfig` dataclass
- `_EventLock` class
- `is_turn_in_progress()`
- `_build_jinja_env()`
- `_render()` (Jinja render helper)

### narrate.py
- `_narrate_messages()` — prompt builder for narrator; accepts `momentum`, `pending_gm_beat` params
- `_known_characters_for_extract()`
- `generate_name_pool()` (moved from old `names.py`)
- `generate_npc_names()` (moved from old `names.py`)

### rules.py (engine/rules.py — NOT ccya/rules.py)
- `_rules_messages()` — prompt builder for rules/intent call
- `_call_rules()` — LLM call wrapper with retry
- `_log_rules_outcome()`

### extraction.py
- `_run_extraction_pipeline()` — runs 3 streams, merges into StateDelta
- `_extract_scene_messages()` — prompt builder for scene extractor
- `_extract_state_messages()` — prompt builder for state extractor
- `_extract_progress_messages()` — prompt builder for progress extractor
- `_call_stream()` — streaming LLM call wrapper

### seed.py
- `generate_seed()` — LLM-generated SeedEnvelope
- `_build_generate_seed_messages()`
- `_soft_validate_seed()`

### changes.py
- `summarize_changes(pre, post, applied, rejected)` → `{inventory, player, facts, quests}`
- `format_change_lines(changes)` → emoji display lines
- `_summarize_applied()`

### pressure.py
- `_expire_scene_pressures()` — post-extraction expiry/urgency escalation for `scene_pressure`

### compactor.py
- `maybe_compact(save_dir, state, config)` — runs compaction if `turn % compact_every == 0`
- `_compact_chronicle()` — LLM call to summarize turns into bullets
- `_build_compact_messages()` — renders compact_system.j2 + compact_user.j2
- `_parse_compact_response()` — extracts bullet lines + JSON events from LLM output
- `_extract_turns_for_compact()` — reads chronicle.md for turns in range
- `_write_compacted_block()` — appends COMPACTED block to chronicle.md

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
- **Stream skipping**: if a scope's `skip_domains` covers all domains owned by a stream, that stream's LLM call is elided entirely. Check `extraction_event["state"]["skipped"]` in events.
- **Delta flow**: three extract results → `StateDelta` → `_validate()` (checks e.g. `inventory_remove` IDs exist, returns `rejections`) → `apply_delta()` (mutates state in-place) → `summarize_changes()` (diffs pre vs post → `changes{inventory, player, facts, quests}`).
