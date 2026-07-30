# AGENTS.md — ccya coding guidance

**CRITICAL:** Read this file first. It is your signpost — it tells you where to go, not what to build.

---

## Runtime context

- **Game server:** `localhost:8765` — turn reviewer at `localhost:8765/turn_reviewer`
- **LLM backend (primary):** `10.75.100.51:1234` — LMStudio, OpenAI-compatible API, `google/gemma-4-26b-a4b-it` on RTX 5070 Ti
- **LLM backend (fallback):** `localhost:8000` — OpenAI-compatible API, Gemma 4-26B via OMLX
- **Makefile:** primary reference for build/lint/run targets

Treat **8k tokens as your effective working context per session.** Do not load more than you need.

Navigation path: 1) This file → 2) `docs/repomap.md` (module index, entry points) → 3) `docs/architecture/OVERVIEW.md` (pipeline overview) → 4) relevant arch subdoc (step2c-record.md, step2d-world.md, pacing-systems.md, state-models.md, etc.) → 5) source files only for the specific functions you are changing.

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

### State model

- `ccya/models/state.py` defines `WorldState` (root Pydantic model) and all section models (`Meta`, `PC`, `Scene`, `NPCEntry`, `Compendium`, `LongTermObjective`, etc.).
- All engine/state functions that read or mutate state take `WorldState` — never `dict[str, Any]`.
- State is **immutable**. Mutation goes through typed mutator methods (`state.set_turn(n)`, `state.add_npc(id, entry)`, etc.) that return a new `WorldState`. Never use `state["key"] = value` or `state.setdefault("key", value)` in engine code.
- I/O: `ccya/state/io.py` — `load_state()`, `save_state()`, `init_save_dir()`, `default_world_state()`.
- Typed mutator list and field routing: see [docs/architecture/state-models.md](docs/architecture/state-models.md).

---

## Code & docs

- **No backwards compatibility required.** Delete unused fields, routes, config keys, models. Don't design migration paths — rip out, replace with new.
- **Documentation — mandatory:** Any code change touching a module, config key, model field, prompt, or public API requires corresponding updates to `docs/architecture/` (pipeline/data shapes), `docs/repomap.md` (module boundaries/APIs), or this file (build/test commands, signposts, conventions). Stale docs are bugs.

---

## Logging

- Use `logging.getLogger(__name__)` — never global loggers.
- Structured logging for new features: turn pipeline phases, state mutations, LLM calls, config changes.
- Follow existing logging patterns.
- Existing infra: `logging_setup.py` (JSONL RotatingFileHandler for `logs/game.log` + console handler).
- Server errors use `ccya.server` logger → `logs/server.log` (rotated) + `saves/server_errors.jsonl` (for turn viewer).
- Config: `server.logging.level` (file, default INFO), `server.logging.console_level` (stdout, default INFO).
- No bare `except: pass` — every exception handler must log at minimum a warning with the exception string.

Log level standards: see `docs/architecture/logging-standards.md`.

---

## Checkers

Just because a checker passes doesn't mean the thing is healthy. It just means it passed a simple deterministic check that signals the thing *might* be healthy and nothing more. Checkers are not a substitute for subjective examination. When validating tickets, use CLI to pull live data from runs and examine it directly — don't rely on checker pass/fail as proof of correctness.

## Test & lint workflow

**Tests are temporarily removed during refactor.** Do not write or reference tests until this phase is complete. All test mentions in docs and code can be ignored for now.

- Run `make check` (lint + typecheck) as a final step when ALL work is complete.
- Do not waste tokens on incremental check runs during implementation.
- `make check` — runs `make lint` (ruff) + `make typecheck` (mypy).

---

## Tickets as Memory

Roadmap tickets (bugs, improvements, features, evals) serve as long-term memory for all work. They are the source of truth that persists across compactions and session boundaries.

**Update tickets continuously.** Whenever you gather new information — findings, fixes, review results — write it to the relevant ticket immediately. Do not buffer findings until the end. Any agent that picks up a ticket should be able to resume from wherever you left off.

`roadmap/` is the canonical ticket tracker. Supersedes Linear as primary source of truth.

- `roadmap/bugs/<slug>.md` — one file per bug
- `roadmap/features/<slug>.md` — one file per feature/moonshot
- `roadmap/improvements/<slug>.md` — one file per improvement (existing thing, better)
- `roadmap/evals/<slug>.md` — one file per eval finding (hybrid bug/improvement)
- `roadmap/archive/` — completed or canceled items
- `roadmap/backlog.md` — auto-generated (scoping, new, validated, triaged) via `make roadmap`
- `roadmap/idea.md` — auto-generated (idea) via `make roadmap`
- `roadmap/active.md` — auto-generated (up-next) via `make roadmap`
- `roadmap/testing.md` — auto-generated (testing) via `make roadmap`
- `roadmap/done.md` — auto-generated (done/canceled) via `make roadmap`
- `roadmap/archive.md` — auto-generated archive TOC via `make roadmap`

**MANDATORY: Every roadmap file must have YAML frontmatter** (title, status, urgency, size, created, ticket_id, optional labels). Files without frontmatter are skipped by `scripts/generate-roadmap.py` with a warning. Schema and status lifecycles: see `roadmap/README.md`.

Creating new tickets: `scripts/new-ticket.py` — interactive prompt for type (bug/feature/improvement/eval) and a single high-level summary. Generates frontmatter with inferred ticket ID, kebab-case slug, and a minimal body. Defaults to urgency: 3, size: medium. Run `make roadmap` after editing the ticket body.

Design docs use a separate status lifecycle:
- `scoping` → `reviewed` → `implemented`
- Set by: create-design (scoping), review-design (reviewed), execute (implemented)

### Ticket IDs

Every roadmap item has a unique ticket ID: `F-N` (features), `B-N` (bugs), `I-N` (improvements), `E-N` (evals). Separate sequences per type. Used in:
- Commit prefixes: `[<slug>] [B-42] <title>: <summary>`
- PR titles: `B-42: <title>`
- Plan/design filenames: `<slug>-<name>.md` with `ticket_id` in frontmatter
- Cross-linking: `design`, `plan`, `pr` frontmatter fields on roadmap files

### Ticket skill

When creating, updating, or auditing roadmap tickets, **always load the `ticket` skill**. It handles type inference, slug generation, ticket ID assignment, template loading, and status transitions. Do not manually edit ticket files or run `new-ticket.py` — use the skill instead.

`new-ticket.py` is a manual CLI fallback for interactive use outside of agent sessions.

---

## Plan lifecycle

- Active plans pending review are in `plans/review/`.
- Active plans approved for execution are in `plans/`.
- Completed plans are in `plans/completed/` (organized by category).
- Move completed plans to `plans/completed/` when done.
- Split large jobs into phases. Aim for at most **3500 lines of code read per phase** to stay within context budget.

## Branch workflow

Only `execute` (code/prompt changes) and `review-code` (PR creation) create branches or worktrees. `create-design`, `plan`, and all review skills work on `main`.

- **Always ask before creating a branch.** Before `execute` creates a worktree, ask: "This plan touches N files. Do you want me to create a branch for this, or should I work on main?" If the user says "no branch", execute on main with a descriptive commit.
- Branch slug is canonical key (from design doc).
- `execute` creates: `git worktree add -b <slug> ../ccya-<slug> main`
- `review-code` opens PR to merge back to `main`.
- Commit prefix: `[<slug>] [<ticket_id>]` (e.g., `[pacing-fix] [B-42]`)
- Authority hierarchy: design doc > plan > source

---

## Execution rules

- **For ev.py:** Always use `.venv/bin/python scripts/debug/ev.py <command> [args...]`. Never use `python3` or `source .venv/bin/activate` — neither works reliably. For `play --llm --turns N`, set bash timeout to at least `N × 60000` ms (~1 minute per turn). Use `--persona` for LLM player presets. See `scripts/debug/README.md` for full docs.
- **For pack validation:** `.venv/bin/python scripts/validate_packs.py [packs_dir]` — loads every pack and validates structural integrity. Exits 1 if any pack fails. Useful for CI/pre-commit/manual verification.
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
- **execute** → execute a plan exactly as written, review changes, commit; asks before creating branch, uses `[<slug>] [<ticket_id>]` commit prefix
- **review-design** → review a design doc against source, update and refine it (single mode); outputs key blockers, ambiguities, improvements
- **review-code** → review a diff or PR for ccya (correctness, contracts, quality); creates PR after review passes
- **ev-run** → iterative eval: 1-5 turns (critical), 10 turns (intermediate), 20-25 turns (balance); phase-gated, skips if no issues found
- **ev-review** → targeted deep dive on specific mechanics, not full rubric pass
- **ev** → general-purpose eval/inspect CLI signpost for ev.py
- **bug-triage** → validate bug candidates, reproduce, assess severity, set `validated` or `canceled`
- **ticket** → create, update, validate, and audit roadmap tickets with enforced standards
- **customize-opencode** → editing opencode's own config/agents/skills/plugins only (not user app code)

---

## Repo map

Read `docs/repomap.md` for module index and entry points.
Read `docs/architecture/` for how things work (pipeline, state models, contracts, prompts).

Cross-cutting tasks:

- Modify turn pipeline → read `docs/architecture/OVERVIEW.md` (pipeline overview) + subdocs (`step0-ruling.md`, `step1-narrate.md`, etc.) for design details; `docs/repomap.md` (5-call pipeline section) for code-level mapping
- Turn pipeline structure: `run_turn()` orchestrator in `turn.py` (~210 lines, down from 667) calls extracted subroutines: `_narrate_phase()` (narration streaming), `_extract_phase()` (extraction pipeline + metrics), `_apply_phase()` (delta application + rejection), `_persist_and_async_cleanup()` (event building, prompt logging, async sanitize/world, save); pipeline order: rules→narrate→extract→apply→persist; end-of-turn async phases (Sanitize + World) after yield("complete")
- Add new config option → read `docs/architecture/OVERVIEW.md` (config section)
- Debug extraction → read `docs/architecture/OVERVIEW.md` (quick reference table) + relevant step subdoc (`step2a-scene.md`, etc.); `docs/repomap.md` (two-channel NPC extraction routing) for code-level mapping
- Debug/inspect events → read `docs/ev/COMMANDS.md` for ev.py commands; `docs/ev/EVAL-RUNS.md` for eval run storage; `docs/ev/CHECKERS.md` for checker docs
- Fast prompt testing → `ev.py prompt-eval dump <save-dir> --turn N --stream STREAM [--from-events]` (render only), `ev.py prompt-eval call <scenario.yaml> [--from-events]` (render + LLM + check; `--from-events` uses stored output, no LLM call); during turns `expected_ms` in `extract_stream_done` events comes from `_avg_event_ms()` reading last 5 entries per stream in `events.jsonl`; first-turn frontend uses fallback estimates: scene 3s, state 3s, record 6s
- Conversation references → `ccya/static/game-utils.js` has extraction row lifecycle: `_showExtractionRow()` (renders 3-bar extraction row), `_activateExtractionBar()` (starts a bar's tick timer), `_completeExtractionBar()` (fills a bar to 100%), `_dismissExtractionRow()` (removes row); pre-stream bar lifecycle: `_showPreStreamBar()` (shows single bar on submit), `_updatePreStreamExpectedMs()` (updates bar's expected duration on `ruling_start`), `_dismissPreStreamBar()` (removes bar on first `narrative_token`); `ccya/static/game.js` SSE phase handler dispatches narrative_token → dismiss pre-stream bar, narrate_done → show extraction row, extract_stream_start → activate bar, extract_stream_done → complete bar; extraction row no longer has an outer grey wrapper (de-wrappered in I-44)
- Run eval scenarios → load `ev` skill for CLI + docs pointers

Any observed inaccuracies in the repomap or documentation should be corrected immediately in the same commit.
