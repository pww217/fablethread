# AGENTS.md — ccya coding guidance

## How to use this file

This file is your **signpost**. It tells you what to do and where to find details.

**Navigation path:**
1. **This file** — rules, workflow, module boundaries
2. **`docs/REPOMAP/`** — where code lives, what each file does, function signatures
3. **`docs/plans/TODO.md`** — what needs to be done, what's done, what's deferred
4. **`docs/plans/`** — detailed plan docs for each feature
5. **`docs/plans/ROADMAP.md`** — priority ordering and exit criteria
6. **The codebase itself** — the source of truth

When working on a task:
- Read the relevant REPOMAP file(s) to understand the code
- Read the TODO item to understand what's expected
- Read the linked plan doc for implementation details
- Then read the actual source files

**When you change code, you must update docs:**
- New files, renamed files, moved functions → update `docs/REPOMAP/`
- New feature, completed item, deferred item → update `docs/plans/TODO.md`
- New module responsibility or boundary → update this file
- Never leave docs stale — if the code changes, the docs must change in the same commit

---

## Module responsibilities — don't cross them

| Module | Owns | Does NOT own |
|---|---|---|
| `engine/` | Turn pipeline: `run_turn()`, extraction, narration, retry logic | State file I/O, HTTP |
| `engine/turn.py` | `run_turn()` orchestrator (thin — imports from submodules) | Helper logic |
| `engine/config.py` | `EngineConfig`, `_EventLock`, `is_turn_in_progress` | Game logic |
| `engine/narrate.py` | Narration prompt building, NPC name generation | State mutation |
| `engine/rules.py` | Rules LLM call wrappers, retry logic | Deterministic dice/bands |
| `engine/extraction.py` | Three-stream extraction pipeline | State mutation |
| `engine/seed.py` | Dynamic seed generation | Game logic |
| `engine/changes.py` | Change summary formatters | LLM calls |
| `engine/pressure.py` | Scene pressure expiry logic | State mutation |
| `engine/compactor.py` | Chronicle compaction + recent_events pruning | State mutation |
| `state/` | State persistence: load, save, apply_delta, append_event, append_chronicle | LLM calls, HTTP |
| `state/io.py` | `load_state`, `save_state`, `init_save_dir`, migration | State mutation logic |
| `state/delta.py` | `apply_delta`, `reconcile_delta`, `PC_CONDITIONS_MAX` | I/O |
| `state/inventory.py` | Inventory ID normalization, fuzzy matching | State mutation |
| `state/npcs.py` | NPC alias map, compendium ordering | State mutation |
| `state/chronicle.py` | Chronicle/events file I/O, `load_recent_chronicle_turns` | State mutation |
| `state/momentum.py` | Momentum tracking | Deterministic dice/bands |
| `models.py` | All Pydantic models, `TurnResult`, `load_config()` | Business logic |
| `server/app.py` | FastAPI app, config bootstrap, Jinja env, startup | Route handlers |
| `server/routes.py` | All `@app.get` / `@app.post` handlers | App bootstrap |
| `server/panels.py` | Debug panel helpers, `_load_*` functions | Route handlers |
| `server/tv.py` | Turn viewer data preparation | Route handlers |
| `server/metrics.py` | Turn metrics, formatting helpers | Route handlers |
| `pack.py` | Pack loading, `PackManifest`, `SeedEnvelope` | State mutation |
| `rules.py` | Deterministic dice: `resolve_check()`, bands, momentum | LLM calls, state |
| `llm_client.py` | LLM HTTP client, chat, streaming, thinking helpers | Prompt construction |
| `eval/` | Eval harness: in-process driver, judge, REPORT.md | State mutation, LLM calls |

If you find logic in the wrong layer, move it rather than pile on.

---

## Prompt rules

- **Do not alter prompts unless explicitly asked to** — if you must, preserve the spirit of the existing wording and intent.

---

## Clean code rules

- **No dead config keys.** If you remove a feature, remove its `config.yaml` key, `EngineConfig` field, and wiring in `server/app.py` in the same PR.
- **No commented-out code.** If something is deferred, track it in `TODO.md` or the plan file; delete it from source.
- **No silent fallbacks that hide bugs.** Prefer an explicit `if key not in state: raise` or a visible warning over silently inventing a default mid-turn.
- **One source of truth per concept.** `meta.turn` is the turn counter. `chronicle.md` is narrative history. `compendium.npcs` is durable NPC identity. Don't replicate these elsewhere.
- **Minimize LLM input tokens.** Every extra token is latency. Audit prompts for: redundant schema duplication, stale context sections, examples that overlap, large narrative echoes.
- **No redundant docstrings or comments.** Remove anything that says what's obvious from the code. Keep only docstrings that explain non-obvious behavior: design decisions, tradeoffs, edge cases, why something is done a certain way, or parameters not obvious from type hints.
- **No section headers (`# --- ... ---`).** Use blank lines and clear function naming instead.
- Type hints are fine — rely on the type checker, not comments, to explain types.
- Fail fast — validate inputs at module boundaries, not deep in logic.
- No `# noqa` / `# type: ignore` unless absolutely unavoidable (document why).

---

## Logging

- Use `logging.getLogger(__name__)` — never global loggers.
- Structured logging for new features: turn pipeline phases, state mutations, LLM calls, config changes.
- Include context keys: `turn`, `trace_id`, `pack`, `kind`.
- Log warnings/errors to SSE errors panel via `_SseErrorHandler`.
- Existing infra: `logging_setup.py` (JSONL file handler + console handler).

---

## Dead code & backwards compatibility

- Remove dead code immediately — no `# legacy` comments, no deferred cleanup.
- No backwards compatibility required. If a field, route, config key, or model is unused: delete it.
- Same PR that removes a feature removes: config key + EngineConfig field + server wiring + tests + docs.
- If migrating state: write a `_migrate_state()` in `state/io.py`, run it once, then delete the migrator.

---

## Test & lint workflow

- Write/update tests as you build features. Change tests when changing behavior.
- Run `make check && make test` only as a final step when ALL work is complete.
- Do not waste tokens on incremental check runs during implementation.
- `make test` — quiet mode (dots + summary). Default for development.
- `make test-v` — verbose output (full tracebacks, test names). For debugging.
- `make test-x` — stop on first failure, verbose. CI-style run.
- `make check` — runs `make lint` (ruff) + `make typecheck` (mypy).
- `make typecheck` — runs mypy on `ccya/`.
- Tests mock the LLM client — never call a real model server.

---

## Plan & TODO/Roadmap lifecycle

- Directories are `docs/plans/` and `docs/plans/ROADMAP.md`.
- Move completed `docs/plans/` to `docs/plans/completed/`.
- Update `docs/plans/TODO.md` when starting work: mark items `[x]` or note status.
- Abandoned items get struck through or moved to a `## Abandoned` section with one-line reason.
- Fix merge conflict markers in `TODO.md` immediately — never leave them.

---

## Planning/Reasoning

- When planning or gathering information to execute a task, split large jobs into segments to preserve your context window. Aim to take in at most 3500 lines of code at time, execute as much as you can, then pause and ask user for input or compaction before the next execution.
- Limit your reasoning to what's necessary. Plan out the process before you begin and stick to it. Keep it as terse as possible, avoid repeating yourself or going in circles.
- When instructed to make a commit, make a detailed memo of all major and key changes.

---

## Execution Rules

- Feel free to curl against a running server (assume it's running) to pull information or rendered templates live to examine.

---

## Known tooling notes

- `pyproject.toml` has `follow_imports = "skip"` in mypy config — prevents pydantic plugin from resolving `BaseModel`. Workaround: `disallow_subclassing_any = false` + per-module `disable_error_code` overrides for `ccya.models`, `ccya.pack`, `ccya.server`.
- Server route handlers use untyped FastAPI decorators (`@app.get`, `@app.post`). Mypy overrides disable `no-untyped-def`, `no-untyped-call`, `untyped-decorator` for `ccya.server`.
- FastAPI `on_event` is deprecated (see `server/app.py`). Migrate to lifespan event handlers when convenient — not blocking.

---

## Repo map

Detailed file/function/directory info lives in `docs/REPOMAP/`. Read the relevant files using your Read tool when the task requires it:

| Working on... | Read |
|---|---|
| Turn pipeline, extractors, retry | `@docs/REPOMAP/engine.md` |
| State persistence, apply_delta | `@docs/REPOMAP/state.md` |
| FastAPI routes, SSE, HTMX | `@docs/REPOMAP/server.md` |
| Pydantic models, TurnResult | `@docs/REPOMAP/models.md` |
| Pack loading, pack modes, name gen | `@docs/REPOMAP/pack.md` |
| Dice, 2d6, bands | `@docs/REPOMAP/rules.md` |
| LLM client, streaming, mock | `@docs/REPOMAP/llm_client.md` |
| Prompt templates | `@docs/REPOMAP/prompts.md` |
| Frontend, CSS, JS, templates | `@docs/REPOMAP/frontend.md` |
| Testing, FakeLLM, commands | `@docs/REPOMAP/testing.md` |
| Config.yaml, EngineConfig | `@docs/REPOMAP/config.md` |
| Directory layout | `@docs/REPOMAP/directory.md` |
| Eval harness | `@docs/REPOMAP/eval.md` |

Cross-cutting tasks (read multiple):
- Modify turn pipeline → `engine.md` + `state.md` + `models.md`
- Add new config option → `config.md` + `engine.md` + `server.md`
- Debug extraction → `engine.md` + `prompts.md` + `state.md`
- New pack → `pack.md` + `models.md`
