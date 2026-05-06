# TODO

Tracking active implementation plans. Each plan lives in its own doc;
this file is the master checklist.

---

## Plan 1: Module Split Refactor

Full detail: [`docs/refactor-plan.md`](refactor-plan.md)

Execute in order — each step leaves the codebase runnable.

### Phase 1 — `state/` package
- [ ] Create `ccya/state/` directory
- [ ] `state/inventory.py` — move normalize/resolve/fuzzy helpers
- [ ] `state/npcs.py` — move `build_npc_alias_map`, `touch_compendium_order`
- [ ] `state/chronicle.py` — move `append_event`, `append_chronicle`, `load_*`
- [ ] `state/momentum.py` — move `apply_momentum`
- [ ] `state/io.py` — move `load_state`, `save_state`, `init_save_dir`, migration logic
- [ ] `state/delta.py` — move `apply_delta`, `reconcile_delta`, `PC_CONDITIONS_MAX`
- [ ] `state/__init__.py` — re-export everything; confirm no external import sites break
- [ ] Delete `ccya/state.py`
- [ ] Smoke test: `python -m ccya` starts without import errors

### Phase 2 — `engine/` package
- [ ] Create `ccya/engine/` directory
- [ ] `engine/config.py` — `EngineConfig`, `_EventLock`, `is_turn_in_progress`
- [ ] `engine/changes.py` — `summarize_changes`, `format_change_lines`
- [ ] `engine/pressure.py` — `_expire_scene_pressures`
- [ ] `engine/narrate.py` — narrate prompt builder; absorb `names.py`
- [ ] `engine/rules.py` — rules LLM call wrappers (NOT `ccya/rules.py` — leave that alone)
- [ ] `engine/extraction.py` — three-stream extraction pipeline
- [ ] `engine/seed.py` — `generate_seed`, seed prompt builders
- [ ] `engine/turn.py` — `run_turn()` orchestrator (thin)
- [ ] `engine/__init__.py` — re-export: `EngineConfig`, `run_turn`, `generate_seed`, `warmup`, `format_change_lines`, `is_turn_in_progress`
- [ ] Delete `ccya/engine.py` and `ccya/names.py`
- [ ] Smoke test: run a full turn end-to-end

### Phase 3 — `server/` package
- [ ] Create `ccya/server/` directory
- [ ] `server/metrics.py` — `_recent_turn_metrics`, `_turn_log_entries`, fmt helpers
- [ ] `server/tv.py` — all `_tv_*` helpers, `_STATUS_CSS`, `_STAGE_CSS`
- [ ] `server/panels.py` — `_debug_context`, `_load_*`, `_get_opening*`
- [ ] `server/app.py` — FastAPI app, config bootstrap, Jinja env, pack loading, `_ERRORS_LOG`, startup, `main()`
- [ ] `server/routes.py` — all `@app.get` / `@app.post` handlers
- [ ] `server/__init__.py` — re-export `app`, `main`
- [ ] Update `ccya/__main__.py` if it imports from `ccya.server` directly
- [ ] Delete `ccya/server.py`
- [ ] Smoke test: server starts, a full UI turn completes

### Phase 4 — Docs
- [ ] Update `REPOMAP.md` with new structure (see refactor-plan.md)
- [ ] Update `AGENTS.md` with per-task routing guide (see refactor-plan.md)

---

## Plan 2: Context Compactor

Full detail: [`docs/compactor-plan.md`](compactor-plan.md)

Execute checkpoints in order A → F. Each checkpoint is independent.

### Checkpoint A — Quest filter (Jinja only)
- [ ] `ccya/prompts/sections/_quests.j2` — filter to `status == 'active'` only; add `(no active quests)` fallback
- [ ] `ccya/prompts/extract_progress_user.j2` — apply same active-only filter to quest list shown to extractor
- [ ] Test: complete a quest, confirm it vanishes from prompt but persists in `state.yaml`

### Checkpoint B — Location description discipline
- [ ] `ccya/prompts/extract_scene_system.j2` — add constraint: only emit `description` on meaningful environmental/tone change; omit if space is unchanged
- [ ] Test: 3 turns same location, no drama — verify `description` absent from turns 2-3 in `events.jsonl`

### Checkpoint C — NPC bio suppression for `recently_left`
- [ ] Find `recently_left` hydration in `ccya/engine.py` (narrate context builder)
- [ ] Strip all fields except `name` and `title` for `recently_left` entries
- [ ] Audit `narrate_user.j2` `recently_left` block — confirm it only renders name/title
- [ ] Test: NPC exits scene → bio absent in prompt; NPC re-enters → bio present

### Checkpoint D — `recent_events` pruner
- [ ] Add `compact_max_event_age: 5` to `config.yaml` under `game:`
- [ ] Implement `prune_recent_events(events, current_turn, state, max_age)` in `ccya/state.py`
- [ ] Call `prune_recent_events` in `run_turn()` after state load, before context build; write pruned list back to state
- [ ] Test: seed 12 events manually, advance 6 turns, verify stale non-relevant events removed; NPC/quest-referenced events kept

### Checkpoint E — Chronicle summarizer (LLM, highest risk)
- [ ] Add `compact_every: 4` to `config.yaml` under `game:`
- [ ] Add `compact_every: int = 0` and `compact_temperature: float = 0.1` to `EngineConfig`
- [ ] Write `ccya/prompts/compact_system.j2` (historian persona, bullet format, relevance anchor instructions)
- [ ] Write `ccya/prompts/compact_user.j2` (renders turns to compact + active quest/NPC/pressure anchors)
- [ ] Implement `compact_chronicle(turns, state, config, llm) -> str` — single low-temp LLM call, returns bullet block
- [ ] Implement `maybe_compact(save_dir, state, config, llm) -> dict` — checks turn % compact_every, calls compact_chronicle + prune_recent_events, updates `state.meta.last_compacted_turn`
- [ ] Create `ccya/engine/compactor.py` (or add to `engine.py` pre-refactor)
- [ ] Call `maybe_compact` in `run_turn()` after state load, before context build
- [ ] Test: play 8 turns; verify chronicle.md has bullet summaries at turns 4 and 8; verify narrate prompt is shorter; verify `last_compacted_turn` updated

### Checkpoint F — Chronicle file size management (post-E only)
- [ ] After checkpoint E is stable, add chronicle trim to `append_chronicle` or compaction pass
- [ ] Keep: all bullet-summary lines + last `window_turns` verbatim blocks
- [ ] Trim: verbatim archive beyond that from top of file
