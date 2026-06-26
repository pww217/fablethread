# AGENTS.md — ccya coding guidance

**CRITICAL:** Read this file first. It is your signpost — it tells you where to go, not what to build.

---

## Runtime context

- **Game server:** `localhost:8765` — turn reviewer at `localhost:8765/turn_reviewer`
- **LLM backend:** `localhost:8080` — OpenAI-compatible API
- **Default model:** Gemma4 — `mlx-community/gemma-4-26b-a4b-it-mxfp8`
- **Dev model:** Qwen3 ~25B-4bit on Apple Silicon (MLX backend)
- **Makefile:** primary reference for build/lint/run targets

Treat **8k tokens as your effective working context per session.** Do not load more than you need.

Navigation path: 1) This file → 2) `docs/repomap.md` (module index, entry points) → 3) `docs/architecture/OVERVIEW.md` (pipeline overview) → 4) relevant arch subdoc (step2c-storytell.md, pacing-systems.md, state-models.md, etc.) → 5) source files only for the specific functions you are changing.

**Context budget per session:** Load AGENTS.md + the relevant `docs/repomap.md` section(s) + one plan doc. Do not read entire source files unless a step requires it. Use `grep` or `curl` against the running server to confirm specific lines rather than reading whole files.

**Plan selection:** If multiple plans are open in `plans/review/` or `plans/`, the user specifies which to execute. If not specified, ask before proceeding.

> **Completed plans:** Live in `plans/completed/`. Before loading any doc from there, verify its status line matches implementation state — `open` means implemented but needs status update; `canceled` means no longer relevant.

**Source vs. plan conflicts:** If source code contradicts a plan doc, trust the source. Note the discrepancy in your commit message and proceed with what source shows.

---

## Prompt rules

- **Do not alter prompts unless explicitly asked to.** If you must, preserve the spirit of the existing wording and intent.
- Prompt templates shared among multiple files should be made in `ccya/prompts/sections/` and included as subtemplates.

### Template disambiguation

Two template systems exist — see `docs/architecture/cross-module-contracts.md` for locations and routing.

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

## Roadmap

`roadmap/` is the canonical ticket tracker. Supersedes Linear as primary source of truth.

- `roadmap/bugs/<slug>.md` — one file per bug
- `roadmap/features/<slug>.md` — one file per feature/improvement/moonshot
- `roadmap/archive/` — completed or canceled items
- `roadmap/backlog.md` — auto-generated backlog TOC (idea/new) via `make roadmap`
- `roadmap/active.md` — auto-generated active TOC (up-next) via `make roadmap`
- `roadmap/done.md` — auto-generated done TOC (done/canceled) via `make roadmap`
- `roadmap/archive-index.md` — auto-generated archive TOC via `make roadmap`

**MANDATORY: Every roadmap file must have YAML frontmatter** (title, status, urgency, size, created, optional labels). Files without frontmatter are skipped by `scripts/generate-roadmap.py` with a warning. Schema and status lifecycles: see `roadmap/README.md`.

Design docs use a separate status lifecycle:
- `scoping` → `reviewed` → `implemented`
- Set by: create-design (scoping), review-design (reviewed), plan (implemented)

---

## Plan lifecycle

- Active plans pending review are in `plans/review/`.
- Active plans approved for execution are in `plans/`.
- Completed plans are in `plans/completed/` (organized by category).
- Move completed plans to `plans/completed/` when done.
- Split large jobs into phases. Aim for at most **3500 lines of code read per phase** to stay within context budget.

## Branch workflow

Only `execute` (code/prompt changes) and `review-code` (PR creation) create branches or worktrees. `create-design`, `plan`, and all review skills work on `main`.

- Branch slug is canonical key (from design doc).
- `execute` creates: `git worktree add -b <slug> ../ccya-<slug> main`
- `review-code` opens PR to merge back to `main`.
- Commit prefix: `[<slug>]`
- Authority hierarchy: design doc > plan > source

---

## Execution rules

- **For ev.py:** Always use `.venv/bin/python scripts/debug/ev.py <command> [args...]`. Never use `python3` or `source .venv/bin/activate` — neither works reliably. For `play --llm --turns N`, set bash timeout to at least `N × 60000` ms (~1 minute per turn). Use `--personality` (not `--persona`) for LLM player presets. See `scripts/debug/README.md` for full docs.
- **For other Python:** Use `.venv/bin/python` directly. `source .venv/bin/activate` does not work reliably in this environment.
- Feel free to `curl` against a running server (assume it's running on `localhost:8765`) to pull rendered templates or live state.
- When stumped by a bug: form one hypothesis, write a minimal `/tmp/` script to test it in isolation, confirm or refute, then act. Do not go in circles.
- When making a commit, write a detailed commit message covering all major and key changes.

---

## Known tooling notes

- Server route handlers use untyped FastAPI decorators (`@app.get`, `@app.post`). Mypy overrides disable `untyped-decorator`, `no-untyped-def`, `no-untyped-call`, `attr-defined`, and `no-any-return` for `ccya.server`.
- Tests are temporarily removed during refactor; this note is deferred until they return.

---

## Cross-skill rules

Defined in full in global AGENTS.md. Key rules:
- Stay in your lane — only touch files the plan or design explicitly names.
- Assume parallel work — never revert code you did not write.
- Authority hierarchy — design doc > plan > source.
- Question tool with recommendation — use `question` tool when ambiguous, recommended option first.

---

## Skills — when to load each

- **create-design** → produce a design doc for a CCYA feature/refactor/problem (no plan/code); lives on `main`
- **plan** → write a complete plan document for a CCYA feature/fix (no execution); includes Design Reference field
- **review-plan** → review a plan doc for correctness before execution; enhanced chat output with plan summary
- **execute** → execute a plan exactly as written, review changes, commit; creates worktree+branch, uses `[<slug>]` commit prefix
- **review-design** → review a design doc against source, update and refine it (single mode); outputs key blockers, ambiguities, improvements
- **review-code** → review a diff or PR for ccya (correctness, contracts, quality); creates PR after review passes
- **ev-run** → launch a full 5-pack eval, run sequentially, produce per-run auto-reports; hands off to ev-review
- **ev-review** → inspect eval runs, check testing items against current run data, run full rubric, update testing bugs to done or up-next, file new bugs as `new`, write consolidated report
- **bug-triage** → validate bug candidates, reproduce, assess severity, set `validated` or `canceled`
- **customize-opencode** → editing opencode's own config/agents/skills/plugins only (not user app code)

---

## Repo map

Read `docs/repomap.md` for module index and entry points.
Read `docs/architecture/` for how things work (pipeline, state models, contracts, prompts).

Cross-cutting tasks:

- Modify turn pipeline → read `docs/architecture/OVERVIEW.md` (pipeline overview) + subdocs (`step0-ruling.md`, `step1-narrate.md`, etc.) for design details; `docs/repomap.md` (5-call pipeline section) for code-level mapping
- Add new config option → read `docs/architecture/OVERVIEW.md` (config section)
- Debug extraction → read `docs/architecture/OVERVIEW.md` (quick reference table) + relevant step subdoc (`step2a-scene.md`, etc.); `docs/repomap.md` (extraction field routing section) for code-level mapping
- Debug/inspect events → read `docs/ev/COMMANDS.md` for ev.py commands; `docs/ev/EVAL-RUNS.md` for eval run storage; `docs/ev/CHECKERS.md` for checker docs
- Fast prompt testing → `ev.py prompt-eval dump <save-dir> --turn N --stream STREAM [--from-events]` (render only), `ev.py prompt-eval call <scenario.yaml> [--from-events]` (render + LLM + check; `--from-events` uses stored output, no LLM call)
- Run eval scenarios → read `scripts/debug/README.md` (eval command section) + `docs/ev/CHECKERS.md`

Any observed inaccuracies in the repomap or documentation should be corrected immediately in the same commit.
