# Workflow Reorganization — Phase 2: Roadmap System & Remaining Gaps

## Purpose

Implement the roadmap ticket tracking system, fix remaining gaps in existing skills, and add the "Assume parallel work" cross-skill rule — then migrate in-repo tracking to all workflow skills.

## Design Reference

`docs/design/workflow-reorganization-design.md`

## Problem Statement

The trunk-based workflow skills have been implemented (worktree lifecycle, PR creation, output standards, review-design consolidation), but three gaps remain: (1) execute runs lint per-phase instead of only at end, (2) plan lacks a chat output section, (3) "Assume parallel work" cross-skill rule is missing. Beyond that, the design doc calls for an in-repo roadmap tracking system (`roadmap/bugs/`, `roadmap/features/`, `roadmap/archive/`, `scripts/generate-roadmap.py`) that all skills must integrate with — none currently do. The ~60 existing Linear tickets must be migrated to roadmap files last.

## Constraints

- Only touch files the plan explicitly names.
- No backwards compatibility — delete old patterns, don't migrate.
- Do not change ev, customize-opencode, or lin skills.
- "Fix all broken checks" is rejected. Keep lint only at end of all phases.
- flesh-design stays deleted (no stub).
- Design doc is gospel — only update if explicitly decided against.
- All question-asking must use the `question` tool with recommended option first.
- `~/.config/opencode/*` external skill files are outside the git repo — committed separately by the user.

## Non-goals

- Does not retroactively convert existing work to roadmap files (except the one-time Linear migration).
- Does not remove or change the lin skill.
- Does not change CCYA pipeline code.
- Does not change ev or customize-opencode skills.
- Does not re-litigate existing workflow decisions (worktree, slug, PR lifecycle, flesh-design deletion).

## Solution

Five phases executed in dependency order: (1) fix three independent pre-roadmap gaps, (2) build the roadmap directory system and generator script, (3) add roadmap status tracking to all five workflow skills, (4) update the local AGENTS.md with roadmap/branch/worktree conventions, (5) one-time migration of ~60 Linear tickets to roadmap files.

## Firm decisions

1. **Linear migration is last.** No roadmap files will be created during the one-time migration until phases 1-4 are complete.
2. **"Fix all broken checks" is rejected.** Lint/typecheck runs only at end of all phases. Per-phase linting in execute must be removed.
3. **"Assume parallel work" is added.** Global AGENTS.md cross-skill rule: never revert code you didn't write, investigate via `git log`, ask user if blocked.
4. **flesh-design stays deleted.** No stub. review-design absorbed its purpose.
5. **roadmap/ is the canonical ticket tracker.** Supersedes Linear as primary source of truth. Linear ticket ref appears in PR body as optional metadata when present in roadmap frontmatter.
6. **roadmap index is auto-generated.** `scripts/generate-roadmap.py` parses YAML frontmatter from all files in `roadmap/bugs/` and `roadmap/features/`, writes `roadmap/index.md`.

## Risks, Ambiguities, and Blockers

- **All skills reference `roadmap/` paths relative to repo root** — ensure consistency (the script and all skill references use the same path).
- **PR body in review-code references roadmap entry** — the roadmap entry slug is the same as the branch slug (design doc slug), so the link is `roadmap/{bugs|features}/<slug>.md`. But the skill needs to determine the subdirectory (bugs vs features). Solution: check for file existence at both paths, or store the type in a well-known location (e.g., the plan doc's frontmatter, or a `roadmap: features/<slug>` field in the plan).
  - **Decision needed:** How does the plan/design doc indicate whether a roadmap entry is in `bugs/` or `features/`? Options: (A) infer from label/type in design doc, (B) add explicit `roadmap_category: bugs|features` field to the plan doc, (C) check both paths at runtime.
- **generate-roadmap.py runs on demand** not on commit hook. The Makefile target runs it. If someone creates roadmap files manually without running the script, the index will be stale.
- **Linear migration is ~60 files** — a mechanical but large task. Estimate: 60 × 5 min = ~5 hours. Should be broken into batches if context-limited.

## Status
`open`

## Phases

5 phases:
1. Pre-roadmap fixes (3 independent changes to execute, plan, global AGENTS.md)
2. Build roadmap system (directories, script, Makefile target)
3. Roadmap integration in all 5 skills (create-design, review-design, plan, execute, review-code)
4. Update local AGENTS.md (roadmap conventions, branch workflow, cross-skill rules)
5. One-time Linear migration (last)

---

## Implementation — Phase 1: Pre-Roadmap Fixes

### Context files to load

- `~/.config/opencode/skills/execute/SKILL.md`
- `~/.config/opencode/skills/plan/SKILL.md`
- `~/.config/opencode/AGENTS.md`

### Detailed steps

#### Step 1.1 — Remove per-phase lint/typecheck from execute

**File:** `~/.config/opencode/skills/execute/SKILL.md`

**What:** Remove step 2c (run lint/typecheck after each phase) and step 2d (run tests after each phase). Move the test run to final verification alongside the existing lint/typecheck at step 3. The lint-only deviation allowance in step 21 stays (that handles fixing existing errors found at final check).

Remove lines 59-60 (per-phase lint sub-step `c.` and test sub-step `d.`). Renumber the remaining sub-step `e.` (line 61) to `c.`. Add a test run to step 3 (line 67) so final verification becomes: "Run the project's lint, type-check, and test commands. All three must pass."

**Why:** The design doc decision table says "Lint/typecheck at end of all phases — run lint + typecheck only at the end of all phases, not per-fix." Tests follow the same pattern: run once at the end rather than after every phase.

**Validation:** After the edit, grep for "lint" and "type-check" in the file. Should show only lines at step 3 (final verification) and the deviation allowance line 21. No occurrence of "After each phase" or per-phase linting. Confirm step 3 includes "lint, type-check, and test commands."

#### Step 1.2 — Add chat output section to plan skill

**File:** `~/.config/opencode/skills/plan/SKILL.md`

**What:** Add a "Chat output" section between the "Plan format" code block (ends line 108) and "When to include a code snippet" (starts line 110) specifying that the agent outputs: design doc reference + phase summary. Model on the existing chat output patterns from other skills (review-plan has a similar section).

Content to add:
```
## Chat output

When complete, output in chat:
- **Design Reference:** Link to the design doc (`docs/design/<slug>-design.md`)
- **Phase summary:** One paragraph summarizing what the plan covers, the number of phases, and the dependency order.
```

**Why:** The design doc's output format standards table specifies plan chat output as "Design doc reference, phase summary." The plan skill currently has no chat output instruction.

**Validation:** Read the file and confirm the Chat output section is present between the Plan format code block and the "When to include a code snippet" section.

#### Step 1.3 — Add "Assume parallel work" cross-skill rule

**File:** `~/.config/opencode/AGENTS.md`

**What:** Add a new cross-skill rule under the existing "Cross-skill Rules" section, after "Authority hierarchy":

```
- **Assume parallel work.** Never revert code you did not write. If a file has changed since you last read it, investigate via `git log` before modifying. If the change conflicts with your work, ask using the `question` tool (recommended option first) rather than overwriting.
```

**Why:** The updated design doc requires this rule. It prevents agents from undoing work from parallel sessions or prior commits.

**Validation:** Read the file and confirm the new rule appears in the Cross-skill Rules section.

### Tests to write or update

None. These are config file edits with no test suite.

---

## Implementation — Phase 2: Build Roadmap System

### Context files to load

- `/Users/pwilson/Repos/ccya/Makefile` (to add `roadmap` target)
- `/Users/pwilson/Repos/ccya/scripts/` directory (to understand existing script patterns)

### Detailed steps

#### Step 2.1 — Create roadmap directory structure

**File:** (multiple directories)

**What:** Create the following directories under repo root:
```
roadmap/
  bugs/
  features/
  archive/
```

If `roadmap/` already exists, skip creation but verify subdirectories exist.

**Why:** The design doc requires `roadmap/bugs/<slug>.md` for bugs, `roadmap/features/<slug>.md` for features/improvements, and `roadmap/archive/` for completed/abandoned items.

**Validation:** `ls roadmap/bugs/ roadmap/features/ roadmap/archive/` — all three exist.

#### Step 2.2 — Create generate-roadmap.py

**File:** `/Users/pwilson/Repos/ccya/scripts/generate-roadmap.py`

**What:** Create a Python script that:
1. Scans `roadmap/bugs/` and `roadmap/features/` for `*.md` files
2. Parses YAML frontmatter from each file (using `yaml` library, or if not available, use a simple regex; prefer `yaml` if `PyYAML` is in the project's dependencies — check with `uv run python -c "import yaml"`)
3. Groups entries by status (scoping, up-next, in-progress, validating, completed, abandoned, backlog, blocked)
4. Within each group, lists entries with: title, slug (filename), type (bug/feature), urgency, size, labels, created date
5. Writes `roadmap/index.md` with: grouped by status, each group as a table, archive items listed separately under "Archive"

Frontmatter schema:
```yaml
---
title: Descriptive title
type: bug | feature
status: scoping | up-next | in-progress | validating | completed | abandoned | backlog | blocked
urgency: 1 | 2 | 3 | 4  (1=highest)
size: small | medium | large | unknown
created: YYYY-MM-DD
completed: YYYY-MM-DD  # optional, only for completed/abandoned
labels:
  - type: improvement | moonshot | balancing | ui | extraction | etc.
  - <other labels>
design: docs/design/<slug>-design.md  # optional
plan: plans/<slug>.md  # optional
linear: TICK-NNN  # optional
---
```

The script should:
- Handle missing frontmatter gracefully (skip file with warning to stderr)
- Sort entries within each status group by urgency (1→4), then by created date (oldest first)
- Skip `index.md` itself (don't try to parse the index)
- Include a note at the top: "Auto-generated by scripts/generate-roadmap.py. Do not edit manually."
- Write the file atomically (write to temp, rename)

Use the project's Python environment: `#!/usr/bin/env python3` shebang, use `pathlib`, `sys`, and `yaml` (or `json` + regex frontmatter parser if yaml unavailable; prefer yaml).

**Why:** The design doc requires an auto-generated TOC grouped by status, driven by a script.

**Validation:** Run `.venv/bin/python scripts/generate-roadmap.py` — should produce `roadmap/index.md` with headers but no entries (directories are empty).

#### Step 2.3 — Add Makefile target

**File:** `/Users/pwilson/Repos/ccya/Makefile`

**What:** Add `roadmap` to the `.PHONY` line and add a new target:
```makefile
roadmap:
	uv run python scripts/generate-roadmap.py
```

Find the right place in the alphabetically-ordered targets (after `new-game` or after `check`).

**Why:** The design doc requires a `make roadmap` target for the auto-generator.

**Validation:** Run `make roadmap` — should produce `roadmap/index.md` (with empty tables).

### Tests to write or update

None. The script is a utility, not library code.

---

## Implementation — Phase 3: Roadmap Integration in Skills

### Context files to load

- `~/.config/opencode/skills/create-design.md/SKILL.md`
- `~/.config/opencode/skills/review-design/SKILL.md`
- `~/.config/opencode/skills/plan/SKILL.md`
- `~/.config/opencode/skills/execute/SKILL.md`
- `~/.config/opencode/skills/review-code/SKILL.md`

### Detailed steps

#### Step 3.1 — Add roadmap file creation to create-design

**File:** `~/.config/opencode/skills/create-design.md/SKILL.md`

**What:** Add a step after worktree creation (step 0) that creates or updates the roadmap file at `roadmap/features/<slug>.md` (default) or `roadmap/bugs/<slug>.md` (if the effort is a bug fix) with status `scoping`. The step infers `features` vs `bugs` from the design doc's type/label if present, or defaults to `features`.

The roadmap file should contain:
```yaml
---
title: <human-readable title from design doc>
type: <bug|feature>
status: scoping
urgency: 3
size: unknown
created: <YYYY-MM-DD>
design: docs/design/<slug>-design.md
labels:
  - <from design doc>
---
```

After creating the file, run `make roadmap` from the repo root to regenerate the index.

**Why:** The design doc requires create-design to create or update the roadmap file with status scoping.

**Validation:** Read the file and confirm the roadmap creation step exists.

#### Step 3.2 — Add roadmap status update to review-design

**File:** `~/.config/opencode/skills/review-design/SKILL.md`

**What:** Add a step at the end of the review process that locates the roadmap file (check `roadmap/features/<slug>.md` first, then `roadmap/bugs/<slug>.md`; use whichever exists) and updates its `status`:
- If the review verdict approves the design (no fatal blockers), set status to `up-next`
- If the review recommends rejection (fatal found), set status to `abandoned`
- After updating, run `make roadmap` from the repo root

**Why:** The design doc requires review-design to update roadmap status: approved → up-next, rejected → abandoned.

**Validation:** Read the file and confirm the roadmap status update step exists.

#### Step 3.3 — Add roadmap status update to plan

**File:** `~/.config/opencode/skills/plan/SKILL.md`

**What:** Add a step at the end of the planning process that locates the roadmap file (check `roadmap/features/<slug>.md` first, then `roadmap/bugs/<slug>.md`; use whichever exists) and updates its `status` field to `up-next`. After updating, run `make roadmap` from the repo root.

**Why:** The design doc requires plan to update roadmap status to up-next.

**Validation:** Read the file and confirm the roadmap status update step exists.

#### Step 3.4 — Add roadmap status update to execute

**File:** `~/.config/opencode/skills/execute/SKILL.md`

**What:** Add a step at the beginning of execution (after worktree verification) that locates the roadmap file (check `roadmap/features/<slug>.md` first, then `roadmap/bugs/<slug>.md`; use whichever exists) and updates its `status` to `in-progress`. Add a step at the end (after lint passes, before commit) that moves the plan to `plans/completed/`, locates the roadmap file, and updates its `status` to `validating`. After each update, run `make roadmap` from the repo root.

The plan file move is already in execute (step "### 4. Mark complete" at lines 71-73). Just add the roadmap status update alongside it.

**Why:** The design doc requires execute to update roadmap status to in-progress, and eventually to validating. Also requires moving the plan to completed/.

**Validation:** Read the file and confirm both roadmap status update steps exist.

#### Step 3.5 — Add roadmap + Linear references to review-code PR body

**File:** `~/.config/opencode/skills/review-code/SKILL.md`

**What:** Update the PR body template in step 9 to include:
1. A link to the roadmap entry. Determine the path by checking `roadmap/features/<slug>.md` first, then `roadmap/bugs/<slug>.md` — use whichever exists. If neither exists, skip the Roadmap section.
2. If the roadmap file's frontmatter has a `linear:` field, include: `Linear: TICK-NNN`. If no `linear:` field, omit the Linear section.

The PR body should become:
```
## Design
docs/design/<slug>-design.md

## Plan
plans/<slug>.md

## Roadmap
roadmap/features/<slug>.md  (or roadmap/bugs/<slug>.md if that path exists)

## Linear
TICK-NNN  (only if present in roadmap frontmatter)
```

Also add a step before PR creation that locates the roadmap file (same features/bugs check), updates its `status` to `validating`, and runs `make roadmap` from the repo root.

**Why:** The design doc requires the PR body to link the roadmap entry and optionally ticket ref. Also requires updating status to validating.

**Validation:** Read the file and confirm the updated PR body template and the status update step.

### Tests to write or update

None. These are config file edits.

---

## Implementation — Phase 4: Update Local AGENTS.md

### Context files to load

- `/Users/pwilson/Repos/ccya/AGENTS.md` (current state)

### Detailed steps

#### Step 4.1 — Add roadmap conventions

**File:** `/Users/pwilson/Repos/ccya/AGENTS.md`

**What:** Add a new "Roadmap" section (before or after the "Plan lifecycle" section) documenting:
- `roadmap/bugs/<slug>.md` — one file per bug
- `roadmap/features/<slug>.md` — one file per feature/improvement/moonshot
- `roadmap/archive/` — completed/abandoned items
- `roadmap/index.md` — auto-generated TOC (via `make roadmap`)
- Status lifecycle: scoping → up-next → in-progress → validating → completed (or abandoned at any point)
- YAML frontmatter schema reference

#### Step 4.2 — Add branch workflow and worktree rules

**File:** `/Users/pwilson/Repos/ccya/AGENTS.md`

**What:** Update the existing "Plan lifecycle" section (or add a new section) to document:
- Branch slug is canonical key (from design doc)
- Worktrees: `git worktree add -b <slug> ../ccya-<slug> main`
- Worktree cleanup after PR merge
- `git branch --show-current` verification at start of every skill
- Commit prefix: `[<slug>]`
- Authority hierarchy: design doc > plan > source

#### Step 4.3 — Add cross-skill rules summary

**File:** `/Users/pwilson/Repos/ccya/AGENTS.md`

**What:** Add a brief reference to the cross-skill rules (defined in full in global AGENTS.md):
- Stay in your lane
- Assume parallel work
- Authority hierarchy
- Question tool with recommendation

**Why:** The design doc requires local AGENTS.md to document roadmap conventions, branch workflow, worktree rules, and cross-skill rules.

**Validation:** Read the file and confirm all three additions are present.

### Tests to write or update

None.

---

## Implementation — Phase 5: One-Time Linear Migration

### Context files to load

- Linear ticket data (via `linearis` CLI)
- `scripts/generate-roadmap.py` (from phase 2)
- Frontmatter schema from phase 2 step 2.2

### Detailed steps

#### Step 5.1 — Export Linear tickets

**What:** Use `linearis` to export all ~60 CCYA project tickets. Capture: title, type (Bug/Feature/Improvement), status, priority, labels, creation date, completion date, description.

**Validation:** Count the output — should be ~60 tickets.

#### Step 5.2 — Generate roadmap files

**What:** For each Linear ticket, create a corresponding `roadmap/bugs/<slug>.md` or `roadmap/features/<slug>.md` file with the YAML frontmatter schema.

Derive the slug from the ticket title (kebab-case). Map:
- Linear type `Bug` → `roadmap/bugs/`
- Linear type `Feature` / `Improvement` → `roadmap/features/`
- Other → `roadmap/features/`

Map Linear priority to urgency:
- Urgent → 1
- High → 2
- Medium → 3
- Low → 4

Map Linear status to roadmap status:
- `New`, `Backlog`, `Idea`, `Scoping` → `backlog`
- `Up Next`, `Accepted` → `up-next`
- `In Progress` → `in-progress`
- `Validating` → `validating`
- `Completed` → `completed`
- `Canceled` → `abandoned`
- `Blocked` → `blocked`

Bulk create the files. After all are created, run `make roadmap` to regenerate the index.

**Validation:** Count files in `roadmap/bugs/` + `roadmap/features/` — should match ~60. `make roadmap` succeeds. `roadmap/index.md` has all entries.

### Tests to write or update

None.
