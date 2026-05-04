# engine.py — turn pipeline

## Public APIs

- **`run_turn(save_dir, user_input, config, template_dir, pack_style, pack_examples, pack_name_locales)`** — Async generator yielding `("token", str)`, `("phase", dict)`, `("complete", TurnResult)`. The 5-call turn pipeline.
- **`generate_seed(pack, config, overrides, template_dir)`** — LLM-generated SeedEnvelope for dynamic packs.
- **`warmup(config)`** — Silent chat call to pre-load model.
- **`is_turn_in_progress(save_dir)`** — Guard against concurrent turns.
- **`EngineConfig`** dataclass — all tunable params (temps, timeouts, token budget, thinking toggles, condition TTL).

## 5-call turn pipeline (run_turn)

1. **Rules / Intent** (Call 0, `llm_chat`, non-streaming) — classifies intent, resolves dice via `rules.resolve_check()`, returns `IntentEnvelope` (scope controls which extractors run) + `RulesOutcome` (band, directive, dice).
2. **Narrate** (Call 1, streaming → SSE → `chronicle.md`) — prose narrative. `RulesOutcome` injected as BINDING block the narrator must not contradict.
3. **Scene Extract** (Call 2a, `llm_chat`, JSON → `SceneExtractResult`) — scene tags, location change, present NPCs, actions, outcome summary.
4. **State Extract** (Call 2b, `llm_chat`, JSON → `StateExtractResult`) — inventory deltas, condition add/remove, failed preconditions.
5. **Progress Extract** (Call 2c, `llm_chat`, JSON → `ProgressExtractResult`) — quest updates, recent events, compendium NPC updates.

Steps 2a–2c merge into `StateDelta` → `_validate()` → `apply_delta()` → `summarize_changes()` → persist (atomic writes: `events.jsonl`, `state.yaml`, `chronicle.md`).

## Internal functions

- `_extract_scene_messages()` — prompt builder for scene extractor (imported by tests)
- `_extract_state_messages()` — prompt builder for state extractor (imported by tests)
- `_extract_progress_messages()` — prompt builder for progress extractor (imported by tests)
- `_run_extraction_pipeline()` — runs 3 streams, merges into StateDelta
- `_validate(state, delta)` — rejects bad inventory_remove IDs, overdraws
- `summarize_changes(pre, post, applied, rejected)` → `{inventory, player, facts, quests}`
- `format_change_lines(changes)` → emoji display lines

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
- **Condition TTL** is controlled by `EngineConfig.condition_ttl_turns` (default `CONDITION_TTL_TURNS = 4`). The engine ticks and removes expired conditions *before* running the extraction pipeline and tells the state stream which IDs it already removed (`engine_expired_conditions`).
- **`events.jsonl`** gains an `extraction` key with per-stream `{rendered_system, rendered_user, output, tokens_in, tokens_out, ms, skipped}` for debugging.
- **Stream skipping**: if a scope's `skip_domains` covers all domains owned by a stream, that stream's LLM call is elided entirely. Check `extraction_event["state"]["skipped"]` in events.
- **Delta flow**: three extract results → `StateDelta` → `_validate()` (checks e.g. `inventory_remove` IDs exist, returns `rejections`) → `apply_delta()` (mutates state in-place) → `summarize_changes()` (diffs pre vs post → `changes{inventory, player, facts, quests}`).
