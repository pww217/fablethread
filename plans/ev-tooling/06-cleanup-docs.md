# Plan 06 — Cleanup + documentation

## Purpose

Delete the old eval harness, rubrics, engine mirror, and Python scenarios. Write the new checker documentation (CHECKERS.md). Update README.md and repomap.md to reflect the new architecture.

## Problem Statement

The old eval code (`ccya/eval/`, `evals/rubrics/`, `evals/scenarios/`, `evals/config.yaml`, `evals/runs/`) still exists and will cause confusion. The engine mirror (`ccya/eval/engine_mirror.py`) duplicates engine constants. The skill file still has inline reference docs that duplicate `scripts/debug/README.md`. Documentation has two sources of truth.

## Constraints

- All old eval code is deleted — no backward compatibility
- No code outside `ccya/eval/` depends on it (verified in design review)
- Documentation has single source of truth: `scripts/debug/README.md` and `docs/ev/CHECKERS.md`
- The ev skill becomes a thin pointer to repo docs

## Non-goals

- Rewriting `scripts/debug/README.md` from scratch — update existing content
- Writing a user manual — CLI --help and README are sufficient

## Solution

Delete 5 directories/filesets. Write CHECKERS.md documenting every checker with ID, type, fields, and examples. Update README.md to cover new commands (play/check/eval). Update repomap.md to reflect ccya/ev/ structure. Update the ev skill to be a thin pointer.

## Firm decisions

- Deletions are permanent. No archived copies. Git history retains the old code.
- Documentation changes are mandatory — stale docs are bugs.

## Risks, Ambiguities, and Blockers

- `evals/scenarios/` has 8 Python files. Are there any external scripts or workflows that reference these paths? (Answer: no — verified in design review, only `ccya/eval/scenario.py` references this path.)
- `evals/runs/` has timestamped run directories. These are evaluation artifacts — safe to delete unless the user wants to keep them for reference. Decision: delete. Git history has them.
- The `.opencode/skills/ev/SKILL.md` file is outside the repo (in `~/.config/opencode/`). Is this file in scope? The design says it becomes a thin pointer. The plan relies on the user updating this file manually, or can we write to it? Mark as manual step.

## Status

`open`

## Implementation

### Context files to load

- `scripts/debug/README.md` (existing docs to update)
- `docs/repomap.md` (architecture overview to update)
- `docs/design/ev-tooling-design.md` (reference for what was built)
- `ccya/ev/checkers/__init__.py` (checker registry for generating CHECKERS.md)
- `ccya/ev/__init__.py` (current command list)

### Detailed steps

#### Step 6.1 — Delete `ccya/eval/` directory

**What:** Remove `ccya/eval/` and all 14 files:
- `__init__.py`, `__main__.py`, `architecture_context.py`, `cli.py`, `config.py`, `engine_mirror.py`, `judge.py`, `pack_utils.py`, `redundancy.py`, `report.py`, `runner.py`, `scenario.py`, `test_eval_schema.py`, `universal_asserts.py`

Use `git rm -r ccya/eval/`.

**Why:** All functionality is replaced by `ccya/ev/`. The old code is tech debt.

**Validation:** `python -c "import ccya.eval"` → ModuleNotFoundError. No remaining imports in the repo reference `ccya.eval` (verified in design review — the only importers were inside `ccya/eval/` itself).

#### Step 6.2 — Delete `evals/rubrics/` directory

**What:** Remove 5 rubric files (1266 lines total): `default.md`, `meta.md`, `narrative_interplay.md`, `prompt_pipeline.md`, `state_correctness.md`.

Use `git rm -r evals/rubrics/`.

**Why:** Replaced by individual checkers in `ccya/ev/checkers/`.

**Validation:** `ls evals/rubrics/` → "No such file or directory".

#### Step 6.3 — Delete `evals/scenarios/` directory

**What:** Remove all Python scenario files:
- `__init__.py`, `baseline.py`, `eval_coverage_gap.py`, `full_cycle.py`, `gm_beat_lifecycle.py`, `momentum_high.py`, `momentum_low.py`, `pressure_lifecycle.py`

Use `git rm -r evals/scenarios/`.

**Why:** Replaced by YAML scenarios loaded by `ev.py eval run`.

**Validation:** `ls evals/scenarios/` → "No such file or directory".

#### Step 6.4 — Delete `evals/config.yaml`

**What:** Remove the eval configuration file.

**Why:** Configuration is now CLI flags on `ev.py eval run`.

**Validation:** `ls evals/config.yaml` → "No such file or directory".

#### Step 6.5 — Delete `evals/runs/` directory

**What:** Remove all past eval run artifacts.

Use `git rm -r evals/runs/`.

**Why:** Replaced by `ev.py eval run` output and `saves/ev/` session storage.

**Validation:** `ls evals/runs/` → "No such file or directory". User can recover past runs from git if needed.

#### Step 6.6 — Write `docs/ev/CHECKERS.md`

**File:** `docs/ev/CHECKERS.md`

**What:** Document the checker library. For each checker in the registry:

```markdown
# Checker Library Reference

## Overview

Each checker is an individual mechanical invariant registered with
`@register_checker`. Deterministic checkers run without an LLM.
LLM checkers use the configured checker model.

## Checkers

### momentum_lifecycle

- **Type:** deterministic
- **Fields:** `ruling.band`, `momentum_before`, `momentum_after`, `applied`
- **What it checks:** Momentum delta matches roll band mapping, values stay within [MOMENTUM_MIN, MOMENTUM_MAX], floor relief respects constraints
- **CLI:** `ev.py check TURN momentum_lifecycle`

### gm_beat_lifecycle
...
```

Generate this list programmatically by running `list_checkers()` and formatting the result, then manual review for prose quality. Each entry should include a usage example and any important caveats.

**Why:** Single source of truth for what each checker does, what it needs, and how to run it.

**Validation:** `ev.py check 5 momentum_lifecycle` — the checker output should reference this document.

#### Step 6.7 — Update `scripts/debug/README.md`

**File:** `scripts/debug/README.md`

**What:** Update the ev.py documentation to cover:
- New subcommands: `play`, `check`, `eval`
- Merged subcommands: `prompt` (subsumes props/compact), `deltas` (subsumes connectors), `mechanics` (subsumes pacing/dice)
- New flags: `--json` on `turn`, `--checker-model` on `check`, `--interactive`/`--llm` on `play`
- New output sections: sanitizer in deltas, extraction context in deltas
- Event shape: document `kind: "sanitizer"` event fields
- Session directory: `saves/ev/<session>/` with `saves/ev/latest` symlink

**Why:** README.md is the canonical user-facing reference. It must stay accurate.

**Validation:** A new user can read README.md and use every ev.py command without confusion.

#### Step 6.8 — Update `docs/repomap.md`

**File:** `docs/repomap.md`

**What:** Update the module boundaries section to reflect:
- `ccya/ev/` — EV tooling package (replaces `ccya/eval/`)
- `ccya/ev/events.py` — Shared data access layer (also consumed by TurnViewer)
- `ccya/ev/checkers/` — Checker library
- `scripts/debug/ev.py` — Thin CLI entry point
- Remove references to `ccya/eval/`, `engine_mirror.py`, `evals/rubrics/`, `evals/scenarios/`
- Add cross-module contract: `ccya/ev/checkers/` imports directly from `ccya/engine/config` and `ccya/rules`

**Why:** repomap.md is the navigation reference for the codebase. Stale entries cause confusion.

#### Step 6.9 — Update the ev skill (manual step)

**File:** `~/.config/opencode/skills/ev/SKILL.md` (outside repo)

**What:** Replace the ~300 lines of inline reference with a thin pointer:

```markdown
# Skill: ev

Read these repo files before using this skill:
- `scripts/debug/README.md` — ev.py command reference, event shape, mechanics sections
- `docs/ev/CHECKERS.md` — checker library documentation
- `docs/architecture/ev-tooling.md` — architecture overview
```

**Why:** Eliminates the second source of truth problem. The skill now points to repo docs instead of duplicating them.

**Note:** This file is in `~/.config/opencode/`, outside the repo. The user must apply this change manually, or we need permission to write outside the workspace.

#### Step 6.10 — Update `AGENTS.md`

**File:** `AGENTS.md` (repo root)

**What:** Update the Repo map section to reflect new `ccya/ev/` paths. Update the "Modify turn pipeline" cross-cutting task reference if it referenced old eval paths. Add new build/test commands if any were introduced (currently none — tests are deferred).

**Why:** AGENTS.md is the navigation signpost. Every code change that touches module boundaries requires its update.

### Tests to write or update

1. Run `make check` (ruff + mypy) — no failures from deleted code or new imports
2. `python scripts/debug/ev.py help` — shows all 13 commands
3. `python scripts/debug/ev.py check --help` — shows checker flags
4. `python -c "from ccya.ev.checkers import list_checkers; print(len(list_checkers()))"` — matches CHECKERS.md count
