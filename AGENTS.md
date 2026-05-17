# AGENTS.md — ccya coding guidance

++**CRITICAL:**++

## How this works

This file is your **signpost**. It tells you what to do and where to find details.

Navigation path: 1) This file → 2) `docs/repomap.md` (module boundaries, public APIs, cross-module contracts) → 3) `/plans/` (plan docs for features and fixes). When working on a task, read repomap.md first, then the linked plan doc, then source files.

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

Read `docs/repomap.md` for module boundaries, public APIs, and cross-module contracts.


Cross-cutting tasks:

- Modify turn pipeline → read docs/repomap.md (5-call pipeline section)
- Add new config option → read docs/repomap.md (EngineConfig + constants sections)
- Debug extraction → read docs/repomap.md (extraction field routing section)

Any observed inaccuracies in the repomap or documentation should be updated immediately.
