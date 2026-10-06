# Fablethread Rename

**Status:** scoping
**Created:** 2026-10-06

## Goal

Replace the `ccya` codename with `Fablethread` everywhere in the active codebase. Historical docs (completed plans, design docs, roadmap tickets, eval runs, findings, logs, saves) are left unchanged.

## Scope

### Out of scope (historical — no changes)
- `plans/completed/` — all completed plans
- `docs/design/` — all design docs
- `roadmap/` — all roadmap tickets
- `evals/` — eval runs and reports
- `docs/releases/` — release notes (historical)
- `docs/discovery/` — discovery docs
- `docs/findings*` — findings
- `docs/linear/` — Linear reference docs
- `saves/` — game saves
- `logs/` — log files
- `tests/` — test files (test filenames and content reference ccya paths)

### In scope (active — rename everywhere)

#### 1. GitHub repo (manual action)
- Rename repo on GitHub: `pww217/ccya` → `pww217/fablethread`
- Update git remote: `git remote set-url origin git@github.com:pww217/fablethread.git`

#### 2. Package directory rename
- `ccya/ccya/` → `ccya/fablethread/` (the inner Python package)

#### 3. Configuration files
- `pyproject.toml`:
  - `name = "ccya"` → `name = "fablethread"`
  - `ccya = "ccya.__main__:main"` → `fablethread = "fablethread.__main__:main"`
  - `known-first-party = ["ccya"]` → `known-first-party = ["fablethread"]`
  - All `[[tool.mypy.overrides]] module = ["ccya.server", ...]` → `["fablethread.server", ...]`
  - All `[[tool.mypy.overrides]] module = ["ccya.rules"]` → `["fablethread.rules"]`
- `Makefile`:
  - `uv run ccya` → `uv run fablethread`
  - `uv run python -m ccya.cli` → `uv run python -m fablethread.cli`
  - `uv run python -m ccya --new-game` → `uv run python -m fablethread --new-game`
  - `uv run mypy ccya` → `uv run mypy fablethread`
  - `ccya/static/app.src.css` → `fablethread/static/app.src.css`
  - `ccya/static/vendor/` → `fablethread/static/vendor/`
  - `mkdir -p ccya/static/vendor` → `mkdir -p fablethread/static/vendor`
  - `curl ... -o ccya/static/vendor/htmx.min.js` → `curl ... -o fablethread/static/vendor/htmx.min.js`
  - `curl ... -o ccya/static/vendor/alpine.min.js` → `curl ... -o fablethread/static/vendor/alpine.min.js`
  - `uv run vulture ccya/` → `uv run vulture fablethread/`

#### 4. AGENTS.md files
- Root `AGENTS.md`:
  - `# AGENTS.md — ccya coding guidance` → `# AGENTS.md — Fablethread coding guidance`
  - All `ccya/` path references → `fablethread/`
  - `ccya/prompts/sections/` → `fablethread/prompts/sections/`
  - `ccya/models/state.py` → `fablethread/models/state.py`
  - `ccya/state/io.py` → `fablethread/state/io.py`
  - `ccya.server` logger → `fablethread.server`
  - `ccya/server` logger → `fablethread/server`
- Note: `ccya/AGENTS.md` does not exist inside the package. Only root `AGENTS.md` needs updating.

#### 5. Python source files (all `.py` files in the package)
- Docstrings: `"""ccya — ..."""` → `"""fablethread — ..."""`
- `from ccya.` imports → `from fablethread.`
- `import ccya.` → `import fablethread.`
- `reload_dirs=["ccya"]` → `reload_dirs=["fablethread"]`
- `sys.modules["ccya.server.app"]` (panels.py:18, routes.py:50) → `sys.modules["fablethread.server.app"]`
- `logging.getLogger("ccya")` (logging_setup.py:16,31) → `logging.getLogger("fablethread")`
- `logging.getLogger("ccya.server")` (logging_setup.py:76) → `logging.getLogger("fablethread.server")`
- `_TEMPLATE_DIR = "ccya/prompts"` (ev/checkers/pacing.py:14, gm_beat.py:13) → `_TEMPLATE_DIR = "fablethread/prompts"`
- `FastAPI(title="ccya", ...)` (server/app.py:171) → `FastAPI(title="fablethread", ...)`
- CLI descriptions: `"ccya — LLM text adventure"` → `"fablethread — LLM text adventure"`
- Banner text: `"  ccya — Choose Your Own Adventure"` → `"  fablethread — Choose Your Own Adventure"`
- `f"ccya — LLM text adventure (dev)"` → `f"fablethread — LLM text adventure (dev)"`
- `"""Structured error types and exception hierarchy for ccya."""` → `"""Structured error types and exception hierarchy for fablethread."""`
- `"""CLI and eval settings for CCYA."""` → `"""CLI and eval settings for Fablethread."""`
- `Engine config lives in ccya/engine/config.py.` → `Engine config lives in fablethread/engine/config.py.`

**Files affected (all in the inner package):**
- `ccya/__init__.py`, `ccya/__main__.py`, `ccya/cli.py`, `ccya/config.py`, `ccya/errors.py`, `ccya/pack.py`, `ccya/rules.py`, `ccya/llm_client.py`, `ccya/logging_setup.py`
- `ccya/engine/` — all `.py` files
- `ccya/engine/extraction/` — all `.py` files
- `ccya/ev/` — all `.py` files
- `ccya/ev/checkers/` — all `.py` files
- `ccya/models/` — all `.py` files
- `ccya/server/` — all `.py` files
- `ccya/state/` — all `.py` files
- `ccya/prompts/context.py`

#### 6. Shell scripts
- `scripts/debug/ev.py:2,11` — docstring `"Delegates to ccya.ev."` → `"Delegates to fablethread.ev."`; `from ccya.ev import main` → `from fablethread.ev import main`
- `scripts/validate_packs.py:15` — `from ccya.pack import load_pack, validate_pack` → `from fablethread.pack import load_pack, validate_pack`
- `scripts/infra/mlx-serve.sh:9` — comment `# from ccya/ root` → `# from fablethread/ root`

#### 7. Static assets (JS)
- `ccya/static/game-utils.js:1` — `CCYA_CARD_KEY` variable name → `FABLETHREAD_CARD_KEY`; `'ccya_card_'` prefix → `'fablethread_card_'`
- `ccya/static/game-utils.js:541` — `'ccya_debug_'` localStorage key → `'fablethread_debug_'`
- `ccya/static/game.js:148-1063` — all `ccya_panel_*` localStorage keys → `fablethread_panel_*`; `ccya_debug_` → `fablethread_debug_`
- Note: JS localStorage keys are user-facing persisting data. Renaming them will reset user's saved panel state on next visit. This is acceptable for a rename.

#### 8. HTML templates
- `ccya/templates/_turn_viewer.html:6` — `<title>Turn Viewer — ccya</title>` → `<title>Turn Viewer — Fablethread</title>`

#### 9. Documentation (active only)
- `docs/architecture/OVERVIEW.md` (2 ccya refs) — `ccya/llm_client.py` paths
- `docs/architecture/cross-module-contracts.md`
- `docs/architecture/narration-ui.md` (multiple) — `ccya/static/` paths
- `docs/architecture/out-of-band.md` — `ccya/pack.py` path
- `docs/architecture/pacing-systems.md` (many) — `ccya/` paths in tables
- `docs/architecture/persist.md` — `ccya/server/`, `ccya/state/` paths
- `docs/architecture/prompts-architecture.md`
- `docs/architecture/state-models.md` — `ccya/models/`, `ccya/state/` paths
- `docs/architecture/step0-ruling.md` — `ccya/engine/turn_context.py` path
- `docs/architecture/step2c-record.md` — `ccya/prompts/context.py` path
- `docs/architecture/turn-viewer-ui.md` — `ccya/static/` path
- `docs/ev/CHECKERS.md`
- `docs/ev/COMMANDS.md`
- `docs/ev/PROMPT-AUDIT.md`
- `docs/ev/RUBRIC.md`
- `docs/repomap.md` (84 ccya refs) — module paths
- `ccya/prompts/SYSTEM_PROMPTING.md:1` — `# SYSTEM PROMPTING — ccya prompt-engineering rules` → `# SYSTEM PROMPTING — Fablethread prompt-engineering rules`
- `ccya/prompts/context.py:17` — `from ccya.models import (...)` → `from fablethread.models import (...)`

All `ccya/` path references → `fablethread/`
All mentions of "ccya" as the project name → "Fablethread"

#### 10. README.md
- Title: `# ccya` → `# Fablethread`
- Description: `A choose-your-own-adventure game backed by a local **mlx-lm** model...` (keep description, just change name)
- `ccya/` in file layout section → `fablethread/`
- `ccya works with any OpenAI-compatible API server` → `Fablethread works with any OpenAI-compatible API server`
- All other ccya references → Fablethread

#### 11. .gitignore
- `ccya/static/app.css` → `fablethread/static/app.css`
- `# ccya/static/vendor/` → `# fablethread/static/vendor/`

### Execution order

1. **Manual:** Rename GitHub repo `pww217/ccya` → `pww217/fablethread`
2. **Rename package dir:** `ccya/ccya/` → `ccya/fablethread/`
3. **Update config files:** `pyproject.toml`, `Makefile`
4. **Update all Python source files:** docstrings, `from ccya.` imports, `sys.modules["ccya.server.app"]`, `logging.getLogger("ccya")`, `_TEMPLATE_DIR = "ccya/prompts"`, `FastAPI(title="ccya")`, CLI strings
5. **Update shell scripts:** path references
6. **Update JS files:** `CCYA_CARD_KEY`, `ccya_*` localStorage keys
7. **Update HTML templates:** title tag
8. **Update active docs:** architecture, ev docs, repomap, prompts
9. **Update AGENTS.md** (root only — no inner package copy exists)
10. **Update README.md**
11. **Update .gitignore**
12. **Update git remote:** `git remote set-url origin git@github.com:pww217/fablethread.git`
13. **Commit:** single commit with all changes
14. **Run `uv sync`:** regenerates `uv.lock`
15. **Delete `ccya-backup-*`:** stale backup directory (cleanup)
16. **Push:** to new repo

### Notes
- Test files are out of scope per the user's instruction, but the test imports will break after this rename. Tests should be updated once they're re-enabled.
