# AGENTS.md — ccya coding guidance

## Module responsibilities — don't cross them

| Module | Owns | Does NOT own |
|---|---|---|
| `engine/` | `run_turn()` generator, `generate_seed()`, retry logic, metrics, cross-stream message building | state file I/O, HTTP |
| `engine/turn.py` | `run_turn()` orchestrator (thin — imports from submodules) | helper logic |
| `engine/config.py` | `EngineConfig` dataclass, `_EventLock`, `is_turn_in_progress` | game logic |
| `engine/narrate.py` | `_narrate_messages()`, NPC name generation | state mutation |
| `engine/rules.py` | `_rules_messages()`, `_call_rules()`, retry logic | deterministic dice/bands |
| `engine/extraction.py` | `_run_extraction_pipeline()`, all `_extract_*_messages`, `_call_stream()` | state mutation |
| `engine/seed.py` | `generate_seed()`, `_build_generate_seed_messages()`, `_soft_validate_seed()` | game logic |
| `engine/changes.py` | `summarize_changes()`, `format_change_lines()`, `_summarize_applied()` | LLM calls |
| `engine/pressure.py` | `_expire_scene_pressures()` | state mutation |
| `state/` | `load_state`, `save_state`, `apply_delta`, `append_event`, `append_chronicle`, `_migrate_state`, `summarize_changes` | LLM calls, HTTP |
| `state/io.py` | `load_state`, `save_state`, `init_save_dir`, state migration | state mutation logic |
| `state/delta.py` | `apply_delta`, `reconcile_delta`, `PC_CONDITIONS_MAX` | I/O |
| `state/inventory.py` | `normalize_inventory_id`, resolve/fuzzy match helpers | state mutation |
| `state/npcs.py` | `build_npc_alias_map`, `touch_compendium_order` | state mutation |
| `state/chronicle.py` | `append_event`, `append_chronicle`, `load_chronicle_tail`, `load_recent_events` | state mutation |
| `state/momentum.py` | `apply_momentum` | deterministic dice/bands |
| `models.py` | all Pydantic models, `TurnResult` dataclass, `load_config()` | business logic |
| `server/app.py` | FastAPI app, config bootstrap, Jinja env, pack loading, startup, `_render`, `_validate_stats` | route handlers |
| `server/routes.py` | All `@app.get` / `@app.post` route handlers | app bootstrap |
| `server/panels.py` | `_debug_context()`, `_load_*` helpers, `_get_opening` | route handlers |
| `server/tv.py` | `_turn_viewer_data()`, `_tv_*` helpers | route handlers |
| `server/metrics.py` | `_recent_turn_metrics()`, `_turn_log_entries()`, fmt helpers | route handlers |
| `pack.py` | `Pack`, `PackManifest`, `SeedEnvelope`, `load_pack()`, `list_packs()`, `parse_world_facts()` | state mutation |
| `rules.py` | `resolve_check()` (2d6 + stat + cond − diff → Band), `SkillName`, `Difficulty`, `Band` | LLM calls, state |
| `llm_client.py` | `chat()`, `chat_stream()` (OpenAI-compatible → `mlx_lm.server`), thinking helpers, token-budget trim | prompt construction |

If you find logic in the wrong layer, move it rather than pile on.

## Prompt rules

- **Do not alter prompts unless explicitly asked to** — if you must, preserve the spirit of the existing wording and intent.

## Clean code rules

- **No dead config keys.** If you remove a feature, remove its `config.yaml` key, `EngineConfig` field, and wiring in `server/app.py` in the same PR.
- **No commented-out code.** If something is deferred, track it in `TODO.md` or the plan file; delete it from source.
- **No silent fallbacks that hide bugs.** Prefer an explicit `if key not in state: raise` or a visible warning over silently inventing a default mid-turn.
- **One source of truth per concept.** `meta.turn` is the turn counter. `chronicle.md` is narrative history. `compendium.npcs` is durable NPC identity. Don't replicate these elsewhere.
- **Minimize LLM input tokens.** Every extra token is latency. Audit prompts for: redundant schema duplication, stale context sections, examples that overlap, large narrative echoes.

## Logging

- Use `logging.getLogger(__name__)` — never global loggers.
- Structured logging for new features: turn pipeline phases, state mutations, LLM calls, config changes.
- Include context keys: `turn`, `trace_id`, `pack`, `kind`.
- Log warnings/errors to SSE errors panel via `_SseErrorHandler`.
- Existing infra: `logging_setup.py` (JSONL file handler + console handler).

## Dead code & backwards compatibility

- Remove dead code immediately — no `# legacy` comments, no deferred cleanup.
- No backwards compatibility required. If a field, route, config key, or model is unused: delete it.
- Same PR that removes a feature removes: config key + EngineConfig field + server wiring + tests + docs.
- If migrating state: write a `_migrate_state()` in `state.py`, run it once, then delete the migrator.

## Test & lint workflow

- Write/update tests as you build features. Change tests when changing behavior.
- Run `make check && make test` only as a final step when ALL work is complete.
- Run `make check && make test` only as a final step when ALL work is complete.
- Do not waste tokens on incremental check runs during implementation.
- `make test` — quiet mode (dots + summary). Default for development.
- `make test-v` — verbose output (full tracebacks, test names). For debugging.
- `make test-x` — stop on first failure, verbose. CI-style run.
- `make check` — runs `make lint` (ruff) + `make typecheck` (mypy).
- `make typecheck` — runs mypy on `ccya/`.
- Tests mock the LLM client — never call a real model server.

## Plan & TODO/Roadmap lifecycle

- Directories are docs/plans/ and docs/ROADMAP.md
- Move completed docs/plans to `docs/plans/completed/`.
- Update `TODO.md` when starting work: mark items `[x]` or note status.
- Abandoned items get struck through or moved to a `## Abandoned` section with one-line reason.
- Fix merge conflict markers in `TODO.md` immediately — never leave them.

## Code quality rules

- **No redundant docstrings or comments.** Remove anything that says what's obvious from the code. Keep only docstrings that explain non-obvious behavior: design decisions, tradeoffs, edge cases, why something is done a certain way, or parameters not obvious from type hints.
- **No section headers (`# --- ... ---`).** Use blank lines and clear function naming instead.
- **No dead config keys.** If you remove a feature, remove its `config.yaml` key, `EngineConfig` field, and wiring in `server/app.py` in the same PR.
- **No commented-out code.** If something is deferred, track it in `TODO.md` or the plan file; delete it from source.
- **No silent fallbacks that hide bugs.** Prefer an explicit `if key not in state: raise` or a visible warning over silently inventing a default mid-turn.
- **One source of truth per concept.** `meta.turn` is the turn counter. `chronicle.md` is narrative history. `compendium.npcs` is durable NPC identity. Don't replicate these elsewhere.
- **Minimize LLM input tokens.** Every extra token is latency. Audit prompts for: redundant schema duplication, stale context sections, examples that overlap, large narrative echoes.
- Type hints are fine — rely on the type checker, not comments, to explain types.
- Fail fast — validate inputs at module boundaries, not deep in logic.
- No `# noqa` / `# type: ignore` unless absolutely unavoidable (document why).

## Planning/Reasoning

- When planning or gathering information to execute a task, split large jobs into segments to preserve your context window. Aim to take in at most 3500 lines of code at time, execute as much as you can, then pause and ask user for input or compaction before the next execution.
- Limit your reasoning to what's necessary. Plan out your process before you begin and stick to it. Keep it as terse as possible, avoid repeating yourself or going in circles. 
- When instructed to make a commit, make a detailed memo of all major and key changes.

## Execution Rules
- Feel free to curl against a running server (assume it's running) to pull information or rendered templates live to examine

## Known tooling notes

- `pyproject.toml` has `follow_imports = "skip"` in mypy config — prevents pydantic plugin from resolving `BaseModel`. Workaround: `disallow_subclassing_any = false` + per-module `disable_error_code` overrides for `ccya.models`, `ccya.pack`, `ccya.server`.
- Server.py route handlers use untyped FastAPI decorators (`@app.get`, `@app.post`). Mypy overrides disable `no-untyped-def`, `no-untyped-call`, `untyped-decorator` for `ccya.server`.
- FastAPI `on_event` is deprecated (see `server/app.py`). Migrate to lifespan event handlers when convenient — not blocking.

## Server module guidance

- Server routes questions → `server/routes.py`
- Debug panel questions → `server/panels.py` + `server/tv.py`
- Server bootstrap/config → `server/app.py`
- Turn metrics → `server/metrics.py`

## Repo map

Detailed file/function/directory info lives in `docs/REPOMAP/`. Read the relevant files using your Read tool when the task requires it:

| Working on... | Read |
|---|---|
| turn pipeline, extractors, retry | `@docs/REPOMAP/engine.md` |
| state.yaml, apply_delta, persistence | `@docs/REPOMAP/state.md` |
| FastAPI routes, SSE, HTMX | `@docs/REPOMAP/server.md` |
| Pydantic models, TurnResult | `@docs/REPOMAP/models.md` |
| pack loading, pack modes, name gen | `@docs/REPOMAP/pack.md` |
| dice, 2d6, bands | `@docs/REPOMAP/rules.md` |
| LLM client, streaming, mock | `@docs/REPOMAP/llm_client.md` |
| prompt templates | `@docs/REPOMAP/prompts.md` |
| frontend, CSS, JS, templates | `@docs/REPOMAP/frontend.md` |
| testing, FakeLLM, commands | `@docs/REPOMAP/testing.md` |
| config.yaml, EngineConfig | `@docs/REPOMAP/config.md` |
| directory layout | `@docs/REPOMAP/directory.md` |

Cross-cutting tasks (read multiple):
- Modify turn pipeline → `engine.md` + `state.md` + `models.md`
- Add new config option → `config.md` + `engine.md` + `server.md`
- Debug extraction → `engine.md` + `prompts.md` + `state.md`
- New pack → `pack.md` + `models.md`
