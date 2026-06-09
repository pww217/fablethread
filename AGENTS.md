# AGENTS.md — ccya coding guidance

**CRITICAL:** Read this file first. It is your signpost — it tells you where to go, not what to build.

---

## Runtime context

Primary development model is **Qwen3 ~25B-4bit on Apple Silicon (MLX backend)**. Treat **8k tokens as your effective working context per session.** Do not load more than you need.

Navigation path: 1) This file → 2) `docs/repomap.md` (module boundaries, public APIs, cross-module contracts) + `docs/architecture/OVERVIEW.md` (pipeline mechanics, data models, flowcharts) → 3) the relevant plan doc in `/plans/review/` or `/plans/` → 4) source files only for the specific functions you are changing.

**Context budget per session:** Load AGENTS.md + the relevant `docs/repomap.md` section(s) + one plan doc. Do not read entire source files unless a step requires it. Use `grep` or `curl` against the running server to confirm specific lines rather than reading whole files.

**Plan selection:** If multiple plans are open in `/plans/review/` or `/plans/`, the user specifies which to execute. If not specified, ask before proceeding.

> **Completed plans:** Live in `/plans/completed/`. Before loading any doc from there, verify its status line matches implementation state — `open` means implemented but needs status update; `abandoned` means no longer relevant.

**Source vs. plan conflicts:** If source code contradicts a plan doc, trust the source. Note the discrepancy in your commit message and proceed with what source shows.

---

## Prompt rules

- **Do not alter prompts unless explicitly asked to.** If you must, preserve the spirit of the existing wording and intent.
- Prompt templates shared among multiple files should be made in `ccya/prompts/sections/` and included as subtemplates.

---

## Clean code rules

- **No commented-out code.**
- **No silent fallbacks that hide bugs.**
- **One source of truth per concept.**
- **Remove dead code immediately.**
- **No redundant docstrings or comments.** Keep only docstrings that explain non-obvious behavior: design decisions, tradeoffs, edge cases, or parameters not obvious from type hints.
- Fail fast — validate inputs at module boundaries, not deep in logic.
- No `# noqa` / `# type: ignore` unless absolutely unavoidable (document why inline).
- **No backwards compatibility required.** If a field, route, config key, or model is unused: delete it. Do not design migration paths and add a bunch of extra code. Just rip out old system, replace with no. Never do backward compatability unless specifically asked.

## Documentation — mandatory update check

Any code change that touches a module, config key, model field, prompt, or public API requires corresponding updates to:
- **`docs/architecture/`** — if pipeline flow, data shapes, or stage contracts change.
- **`docs/repomap.md`** — if module boundaries, function signatures, or public APIs change.
- **`AGENTS.md`** (this file itself) — if build commands, test commands, signposts, or repo conventions change.

These are not optional. Every plan, execution, and code review must include a documentation assessment. Stale docs are bugs.

---

## Logging

- Use `logging.getLogger(__name__)` — never global loggers.
- Structured logging for new features: turn pipeline phases, state mutations, LLM calls, config changes.
- Follow existing logging patterns.
- Existing infra: `logging_setup.py` (JSONL file handler + console handler).

### Log level standards

| Level | When to use | Required extra context |
|---|---|---|
| `DEBUG` | Detailed trace: per-step timing, LLM call start/end, token counts, conditional branches, truncation details | Pipeline: `trace_id`, `turn` |
| `INFO` | Phase boundaries: pipeline start/end per turn, compaction trigger, state save/load, server startup | Pipeline: `trace_id`, `turn`; State: `save_dir`; Server: `save`, `turn` |
| `WARNING` | Recoverable anomalies: malformed data skipped, non-critical parse failures, deprecated paths, LLM retries | Pipeline: `trace_id`, `turn`, `error_kind`; State: `save_dir`; Server: `save`, `turn`, `error_kind` |
| `ERROR` | Definitive failures: LLM call hard failure, state load failure, migration failure, critical parse failures | Same as WARNING + `exc_info` |
| `EXCEPTION` | Use `_log.exception()` in `except` blocks where we cannot recover | Same as WARNING |

- No bare `except: pass` — every exception handler must log at minimum a warning with the exception string.

---

## Test & lint workflow

**Tests are temporarily removed during refactor.** Do not write or reference tests until this phase is complete. All test mentions in docs and code can be ignored for now.

- Run `make check` (lint + typecheck) as a final step when ALL work is complete.
- Do not waste tokens on incremental check runs during implementation.
- `make check` — runs `make lint` (ruff) + `make typecheck` (mypy).

---

## Plan lifecycle

- Active plans pending review are in `/plans/review/`.
- Active plans approved for execution are in `/plans/`.
- Completed plans are in `/plans/completed/` (organized by category).
- Move completed plans to `/plans/completed/` when done.
- Split large jobs into phases. Aim for at most **3500 lines of code read per phase** to stay within context budget.

---

## Execution rules

- **Always activate the venv before running Python directly:** `source .venv/bin/activate`. System Python (3.9) is too old — project requires 3.11+.
- Feel free to `curl` against a running server (assume it's running on `localhost:8000`) to pull rendered templates or live state.
- When stumped by a bug: form one hypothesis, write a minimal `/tmp/` script to test it in isolation, confirm or refute, then act. Do not go in circles.
- When making a commit, write a detailed commit message covering all major and key changes.

---

## Known tooling notes

- Server route handlers use untyped FastAPI decorators (`@app.get`, `@app.post`). Mypy overrides disable `untyped-decorator`, `no-untyped-def`, `no-untyped-call`, `attr-defined`, and `no-any-return` for `ccya.server`.
- Tests are temporarily removed during refactor; this note is deferred until they return.
---

---

## Skills — when to load each

- **create-design** → produce a design doc for a CCYA feature/refactor/problem (no plan/code)
- **flesh-design** → review & sharpen an existing design doc against source (no plan/code)
- **plan** → write a complete plan document for a CCYA feature/fix (no execution)
- **review-plan** → review a plan doc for correctness before execution
- **execute** → execute a plan exactly as written, review changes, commit
- **review-code** → review a diff or PR for ccya (correctness, contracts, quality; no fixes)
- **ev** → inspect turn data from events.jsonl using ev.py (debug pipeline turns)
- **customize-opencode** → editing opencode's own config/agents/skills/plugins only (not user app code)

---

## Repo map

Read `docs/repomap.md` for module boundaries, public APIs, and cross-module contracts.

Cross-cutting tasks:

- Modify turn pipeline → read `docs/architecture/OVERVIEW.md` (pipeline overview) + subdocs (`step0-ruling.md`, `step1-narrate.md`, etc.) for design details; `docs/repomap.md` (5-call pipeline section) for code-level mapping
- Add new config option → read `docs/repomap.md` (EngineConfig + constants sections)
- Debug extraction → read `docs/architecture/OVERVIEW.md` (quick reference table) + relevant step subdoc (`step2a-scene.md`, etc.); `docs/repomap.md` (extraction field routing section) for code-level mapping

Any observed inaccuracies in the repomap or documentation should be corrected immediately in the same commit.