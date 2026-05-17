# AGENTS.md — ccya coding guidance

++**CRITICAL:**++

- Be as terse as possible in your thinking and token use, answer immediately and directly
- If unsure about anything or making a major decision that's hard to reverse, ask the user for guidance always.
- **🛑 Critical Anti-Looping & Overthinking Directives**
You are an efficient problem solver. Avoid infinite reasoning loops and overthinking. Follow these strict rules:
  1. **Time/Token Cap:** If your internal reasoning reaches [2,000] tokens or becomes circular, immediately halt internal refining and output the best current solution.
  2. **Anti-Looping:** If you find yourself re-evaluating the same variables or returning to the same tool/method, stop, acknowledge the impasse, and present a fallback option.
  3. **Action Over Theory:** For coding or agentic tasks, lean on external tool execution (if available) rather than endless internal simulations. Do not repeatedly "re-verify" the same code without making changes.
  4. **Hard Stop:** Once a clear, actionable conclusion is reached, finalize the output immediately. Avoid unnecessary summarizing or meta-commentary about your thought process.

## How to use this file

This file is your **signpost**. It tells you what to do and where to find details.

**Navigation path:**

1. **This file** — rules, workflow, module boundaries
2. `**docs/REPOMAP/`** — where code lives, what each file does, function signatures
3. `**/plans/`** — plan docs for features and fixes
4. **The codebase itself** — the source of truth

When working on a task:

- Read the relevant REPOMAP file(s) to understand the code
- Read the linked plan doc for implementation details
- Then read the actual source files

**When you change code, you must update docs:**

- New files, renamed files, moved functions → update `docs/REPOMAP/`
- New module responsibility or boundary → update this file
- Never leave docs stale — if the code changes, the docs must change in the same commit

---

## Module responsibilities — don't cross them


| Module                 | Owns                                                                       | Does NOT own              |
| ---------------------- | -------------------------------------------------------------------------- | ------------------------- |
| `engine/`              | Turn pipeline: `run_turn()`, extraction, narration                         | State file I/O, HTTP      |
| `engine/turn.py`       | `run_turn()` orchestrator (thin — imports from submodules)                 | Helper logic              |
| `engine/config.py`     | `EngineConfig`, `_EventLock`, `is_turn_in_progress`                        | Game logic                |
| `engine/narrate.py`    | Narration prompt building, NPC name generation                             | State mutation            |
| `engine/rules.py`      | Rules LLM call wrappers, retry logic                                       | Deterministic dice/bands  |
| `engine/extraction.py` | Three-stream extraction pipeline                                           | State mutation            |
| `engine/seed.py`       | Dynamic seed generation                                                    | Game logic                |
| `engine/changes.py`    | Change summary formatters                                                  | LLM calls                 |
| `engine/pressure.py`   | Scene pressure expiry logic                                                | State mutation            |
| `engine/compactor.py`  | Chronicle compaction + recent_events pruning                               | State mutation            |
| `state/`               | State persistence: load, save, apply_delta, append_event, append_chronicle | LLM calls, HTTP           |
| `state/io.py`          | `load_state`, `save_state`, `init_save_dir`, migration                     | State mutation logic      |
| `state/delta.py`       | `apply_delta`, `reconcile_delta`, `PC_CONDITIONS_MAX`                      | I/O                       |
| `state/inventory.py`   | Inventory ID normalization, fuzzy matching                                 | State mutation            |
| `state/npcs.py`        | NPC alias map, compendium ordering                                         | State mutation            |
| `state/chronicle.py`   | Chronicle/events file I/O, `load_recent_chronicle_turns`                   | State mutation            |
| `state/momentum.py`    | Momentum tracking                                                          | Deterministic dice/bands  |
| `models.py`            | All Pydantic models, `TurnResult`, `load_config()`                         | Business logic            |
| `server/app.py`        | FastAPI app, config bootstrap, Jinja env, startup                          | Route handlers            |
| `server/routes.py`     | All `@app.get` / `@app.post` handlers                                      | App bootstrap             |
| `server/panels.py`     | Debug panel helpers, `_load`_* functions                                   | Route handlers            |
| `server/tv.py`         | Turn viewer data preparation                                               | Route handlers            |
| `server/metrics.py`    | Turn metrics, formatting helpers                                           | Route handlers            |
| `pack.py`              | Pack loading, `PackManifest`, `SeedEnvelope`                               | State mutation            |
| `rules.py`             | Deterministic dice: `resolve_check()`, bands, momentum                     | LLM calls, state          |
| `llm_client.py`        | LLM HTTP client, chat, streaming, thinking helpers                         | Prompt construction       |
| `eval/`                | Eval harness: in-process driver, judge, REPORT.md                          | State mutation, LLM calls |


If you find logic in the wrong layer, move it rather than pile on.

---

## Prompt rules

- **Do not alter prompts unless explicitly asked to** — if you must, preserve the spirit of the existing wording and intent.

---

## Clean code rules

- **No dead config keys.** If you remove a feature, remove its `config.yaml` key, `EngineConfig` field, and wiring in `server/app.py` in the same PR.
- **No commented-out code.** If something is deferred, track it in the plan file; delete it from source.
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

- Critical: Always update tests to reflect the code, never the code to reflect the tests!!
- Write/update tests as you build features. 
- Run `make check && make test` only as a final step when ALL work is complete.
- Do not waste tokens on incremental check runs during implementation.
- `make test` — quiet mode (dots + summary). Default for development. Don't try to truncate output here, it will only return `.......`. Run make test in full.
- `make test-v` — verbose output (full tracebacks, test names). For debugging.
- `make test-x` — stop on first failure, verbose. CI-style run.
- `make check` — runs `make lint` (ruff) + `make typecheck` (mypy).
- `make typecheck` — runs mypy on `ccya/`.
- Tests mock the LLM client — never call a real model server.

---

## Plan lifecycle

- Active plans are in `/plans/`, completed plans in `/plans/completed/` (organized by category).
- Plans awaiting review are in `/plans/review/` — these must NOT be executed. They need a review pass first.
- Move completed plans from `/plans/` to `/plans/completed/` (organized by category).
- Abandoned plans get an `## Abandoned` section with one-line reason.
- Split large jobs into segments. Aim for at most 3500 lines of code per segment.

---

## Execution Rules

- Feel free to curl against a running server (assume it's running) to pull information or rendered templates live to examine.
- When stumped by a bug, create a hypothesis and test it in isolation; don't go in circles. Use the scientific method.
- When instructed to make a commit, make a detailed memo of all major and key changes.

---

## Known tooling notes

- `pyproject.toml` has `follow_imports = "skip"` in mypy config — prevents pydantic plugin from resolving `BaseModel`. Workaround: `disallow_subclassing_any = false` + per-module `disable_error_code` overrides for `ccya.models`, `ccya.pack`, `ccya.server`.
- Server route handlers use untyped FastAPI decorators (`@app.get`, `@app.post`). Mypy overrides disable `no-untyped-def`, `no-untyped-call`, `untyped-decorator` for `ccya.server`.
- FastAPI `on_event` is deprecated (see `server/app.py`). Migrate to lifespan event handlers when convenient — not blocking.
- When running tests, use a killswitch of 15 seconds. If it fails, it sometimes hangs indefinitely.

---

## Repo map

Detailed file/function/directory info lives in `docs/REPOMAP/`. Read the relevant files using your Read tool when the task requires it:


| Working on...                      | Read                          |
| ---------------------------------- | ----------------------------- |
| Turn pipeline, extractors, retry   | `@docs/REPOMAP/engine.md`     |
| State persistence, apply_delta     | `@docs/REPOMAP/state.md`      |
| FastAPI routes, SSE, HTMX          | `@docs/REPOMAP/server.md`     |
| Pydantic models, TurnResult        | `@docs/REPOMAP/models.md`     |
| Pack loading, pack modes, name gen | `@docs/REPOMAP/pack.md`       |
| Dice, 2d6, bands                   | `@docs/REPOMAP/rules.md`      |
| LLM client, streaming, mock        | `@docs/REPOMAP/llm_client.md` |
| Prompt templates                   | `@docs/REPOMAP/prompts.md`    |
| Frontend, CSS, JS, templates       | `@docs/REPOMAP/frontend.md`   |
| Testing, FakeLLM, commands         | `@docs/REPOMAP/testing.md`    |
| Config.yaml, EngineConfig          | `@docs/REPOMAP/config.md`     |
| Directory layout                   | `@docs/REPOMAP/directory.md`  |
| Eval harness                       | `@docs/REPOMAP/eval.md`       |


Cross-cutting tasks (read multiple):

- Modify turn pipeline → `engine.md` + `state.md` + `models.md`
- Add new config option → `config.md` + `engine.md` + `server.md`
- Debug extraction → `engine.md` + `prompts.md` + `state.md`
- New pack → `pack.md` + `models.md`

Any observed inaccuracies in the repomap or documentation should be updated immediately.