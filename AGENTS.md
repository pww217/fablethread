# AGENTS.md — ccya coding guidance

**CRITICAL:** Read this file first. It is your signpost — it tells you where to go, not what to build.

---

## Runtime context

Primary development model is **Qwen3 ~25B-4bit on Apple Silicon (MLX backend)**. Treat **8k tokens as your effective working context per session.** Do not load more than you need.

Navigation path: 1) This file → 2) `docs/repomap.md` (module boundaries, public APIs, cross-module contracts) + `docs/architecture/OVERVIEW.md` (pipeline mechanics, data models, flowcharts) → 3) the relevant plan doc in `plans/review/` or `plans/` → 4) source files only for the specific functions you are changing.

**Context budget per session:** Load AGENTS.md + the relevant `docs/repomap.md` section(s) + one plan doc. Do not read entire source files unless a step requires it. Use `grep` or `curl` against the running server to confirm specific lines rather than reading whole files.

**Plan selection:** If multiple plans are open in `plans/review/` or `plans/`, the user specifies which to execute. If not specified, ask before proceeding.

> **Completed plans:** Live in `plans/completed/`. Before loading any doc from there, verify its status line matches implementation state — `open` means implemented but needs status update; `abandoned` means no longer relevant.

**Source vs. plan conflicts:** If source code contradicts a plan doc, trust the source. Note the discrepancy in your commit message and proceed with what source shows.

---

## Prompt rules

- **Do not alter prompts unless explicitly asked to.** If you must, preserve the spirit of the existing wording and intent.
- Prompt templates shared among multiple files should be made in `ccya/prompts/sections/` and included as subtemplates.

### Template disambiguation

Two entirely separate template systems exist — do not conflate them:

| System | Location | Purpose | Engine |
|---|---|---|---|
| **Prompt templates** | `ccya/prompts/` (`.j2`) | Render LLM messages (system/user prompts) | Jinja2 via `_render()` in `narrate.py` / `extraction.py` |
| **UI templates** | `ccya/templates/` (`.html`) | Render browser HTML (sidebars, modals, character sheets) | Jinja2 via FastAPI `_render()` in `server/routes.py` |

NPC routing: see `docs/repomap.md`.

---

## Code & docs

- **No backwards compatibility required.** Delete unused fields, routes, config keys, models. Don't design migration paths — rip out, replace with new.
- **Documentation — mandatory:** Any code change touching a module, config key, model field, prompt, or public API requires corresponding updates to `docs/architecture/` (pipeline/data shapes), `docs/repomap.md` (module boundaries/APIs), or this file (build/test commands, signposts, conventions). Stale docs are bugs.

---

## Logging

- Use `logging.getLogger(__name__)` — never global loggers.
- Structured logging for new features: turn pipeline phases, state mutations, LLM calls, config changes.
- Follow existing logging patterns.
- Existing infra: `logging_setup.py` (JSONL file handler + console handler).
- No bare `except: pass` — every exception handler must log at minimum a warning with the exception string.

Log level standards: see `docs/architecture/logging-standards.md`.

---

## Test & lint workflow

**Tests are temporarily removed during refactor.** Do not write or reference tests until this phase is complete. All test mentions in docs and code can be ignored for now.

- Run `make check` (lint + typecheck) as a final step when ALL work is complete.
- Do not waste tokens on incremental check runs during implementation.
- `make check` — runs `make lint` (ruff) + `make typecheck` (mypy).

---

## Plan lifecycle

- Active plans pending review are in `plans/review/`.
- Active plans approved for execution are in `plans/`.
- Completed plans are in `plans/completed/` (organized by category).
- Move completed plans to `plans/completed/` when done.
- Split large jobs into phases. Aim for at most **3500 lines of code read per phase** to stay within context budget.

---

## Execution rules

- **For ev.py:** Always use `.venv/bin/python scripts/debug/ev.py <command> [args...]`. Never use `python3` or `source .venv/bin/activate` — neither works reliably. For `play --llm --turns N`, set bash timeout to at least `N × 60000` ms (~1 minute per turn). Use `--personality` (not `--persona`) for LLM player presets. See `scripts/debug/README.md` for full docs.
- **For other Python:** Use `.venv/bin/python` directly. `source .venv/bin/activate` does not work reliably in this environment.
- Feel free to `curl` against a running server (assume it's running on `localhost:8000`) to pull rendered templates or live state.
- When stumped by a bug: form one hypothesis, write a minimal `/tmp/` script to test it in isolation, confirm or refute, then act. Do not go in circles.
- When making a commit, write a detailed commit message covering all major and key changes.

---

## Known tooling notes

- Server route handlers use untyped FastAPI decorators (`@app.get`, `@app.post`). Mypy overrides disable `untyped-decorator`, `no-untyped-def`, `no-untyped-call`, `attr-defined`, and `no-any-return` for `ccya.server`.
- Tests are temporarily removed during refactor; this note is deferred until they return.

---

## Linear issue tracking

Project: CCYA | Team: PW (Peter) | Ticket IDs: TICK- (e.g., TICK-52)

Labels: type (`Bug`, `Feature`, `Improvement`) + bucket (`World Building`, `Extraction`, `UI`, `Balancing`, `Tooling`, `Tech Debt`)
Priority: 1=urgent, 2=high, 3=medium, 4=low

Status lifecycle:
- Bugs: `New` → `Accepted` → `In Progress` → `Validating` → `Completed`
- Non-bugs: `Idea` → `Backlog` → `Scoping` → `Up Next` → `In Progress` → `Validating` → `Completed`
- Validating is mandatory unless explicitly overridden
- All: Can be canceled at any stage

Tickets live under bucket parent issues. Use title prefixes to disambiguate subsystem: `[Scene]`, `[State]`, `[Storytell]`, `[Narrator]`, `[Ruling]`, `[NPC]`, `[Conditions]`, `[Prompt]`, `[EV]`, `[Infra]`. See `plans/completed/linear-reorganization.md` for the full table.

`linearis` is installed globally at `/opt/homebrew/bin/linearis` — available in PATH, not in the venv. Use it (not `linear`) for all CLI operations. Load the `linear` skill for commands and workflow guidance. Always search for existing tickets before creating new ones. Always associate tickets with the CCYA project.

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
- Add new config option → read `docs/repomap.md` (EngineConfig + constants section)
- Debug extraction → read `docs/architecture/OVERVIEW.md` (quick reference table) + relevant step subdoc (`step2a-scene.md`, etc.); `docs/repomap.md` (extraction field routing section) for code-level mapping
- Debug/inspect events → read `scripts/debug/README.md` for ev.py commands; `docs/ev/CHECKERS.md` for checker docs
- Run eval scenarios → read `scripts/debug/README.md` (eval command section) + `docs/ev/CHECKERS.md`

Any observed inaccuracies in the repomap or documentation should be corrected immediately in the same commit.