# AGENTS.md — ccya coding guidance

++**CRITICAL:**++

- Be as terse as possible in your thinking and token use, answer immediately and directly
- If unsure about anything or making a major decision that's hard to reverse, ask the user for guidance always.
- You **never** deviate from a plan without informing the user about what, why, and how your solution is better.
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

## Prompt rules

- **Do not alter prompts unless explicitly asked to** — if you must, preserve the spirit of the existing wording and intent.
- Prompt templates that are shared among multiple files should be made in ccya/prompts/sections/ and then included in the prompts as a subtemplate.

---

## Clean code rules

- **No commented-out code.**
- **No silent fallbacks that hide bugs.**
- **One source of truth per concept.**
- **Remove dead code immediately**
- **No redundant docstrings or comments.** Remove anything that says what's obvious from the code. Keep only docstrings that explain non-obvious behavior: design decisions, tradeoffs, edge cases, why something is done a certain way, or parameters not obvious from type hints.
- Fail fast — validate inputs at module boundaries, not deep in logic.
- No `# noqa` / `# type: ignore` unless absolutely unavoidable (document why).
- **No backwards compatibility required.** If a field, route, config key, or model is unused: delete it.

---

## Logging

- Use `logging.getLogger(__name__)` — never global loggers.
- Structured logging for new features: turn pipeline phases, state mutations, LLM calls, config changes.
- Follow existing logging patterns
- Existing infra: `logging_setup.py` (JSONL file handler + console handler).

---

## Test & lint workflow

- Critical: Always update tests to reflect the code, never the code to reflect the tests!!
- Write/update tests as you build features. 
- Run `make check && make test` only as a final step when ALL work is complete.
- Do not waste tokens on incremental check runs during implementation.
- `make test` — quiet mode (dots + summary). Default for development. Don't try to truncate/pipe output here, it will only return `.......`. 
- `make check` — runs `make lint` (ruff) + `make typecheck` (mypy).
- Tests mock the LLM client (FakeLLM) — never call a real model server.

---

## Plan lifecycle

- Active plans are in `/plans/` (may be empty if all plans are completed/reviewed).
- Completed plans are in `/plans/completed/` (organized by category).
- Move completed plans from `/plans/` to `/plans/completed/` (organized by category).
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
| Debug scripts, events.jsonl CLI    | `@scripts/debug/README.md`    |
| Eval harness                       | `@docs/REPOMAP/eval.md`       |
| Seed generation                    | `@docs/REPOMAP/seed.md`       |


Cross-cutting tasks (read multiple):

- Modify turn pipeline → `engine.md` + `state.md` + `models.md`
- Add new config option → `config.md` + `engine.md` + `server.md`
- Debug extraction → `engine.md` + `prompts.md` + `state.md`
- New pack → `pack.md` + `models.md`

Any observed inaccuracies in the repomap or documentation should be updated immediately.