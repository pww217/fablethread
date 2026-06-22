# Workflow Reorganization

## Purpose

Implement trunk-based development workflow across all ccya skills, AGENTS.md files, and OpenCode config.

## Problem Statement

The current workflow has no trunk-based discipline. All work lands directly on `main` with no feature branches, no PRs, and no audit trail linking design docs → plans → commits. Multiple skills (flesh-design, review-design) overlap in purpose with no clear boundary, and their output is not human-readable. There is no mechanism to prevent agents from touching files outside their planned scope.

## Constraints

- The agent works in a single working directory per session. Worktrees must be created and entered into deliberately.
- Do not change the ev or customize-opencode skills.
- Do not remove the lin skill.
- Do not change the content or structure of CCYA pipeline code.
- Do not retroactively convert existing work to branches.

## Non-goals

- Does not change the ev or customize-opencode skills.
- Does not remove the lin skill.
- Does not change CCYA pipeline code.
- Does not retroactively convert existing work to branches.

## Solution

This plan implements trunk-based development by adding worktree+branch lifecycle to skills, consolidating flesh-design into review-design, adding cross-skill rules, standardizing output formats, and adding PR creation to review-code.

## Firm decisions

1. Branch slug is the canonical key — used in design doc filenames, plan doc filenames, commit prefixes, and PR title.
2. Slug is set in the design doc. Worktree+branch is created during execute (after plan), not during create-design.
3. Worktree per branch: `git worktree add -b <slug> ../ccya-<slug> main` at the start of execute.
4. Worktree cleanup after PR merge.
5. PR created at end of review-code with `gh pr create`.
6. Merge to main via PR. Human approves and merges. No auto-merge.
7. flesh-design deleted. No stub.
8. review-design single mode: update and refine existing design doc, surfacing key blockers, design ambiguities, and suggested improvements.
9. "Stay in your lane" cross-skill rule added to global AGENTS.md.
10. Authority hierarchy: design doc > plan > source.
11. Lint/typecheck only at end of all phases, not per-fix.

## Risks, Ambiguities, and Blockers

- **Worktree creation fails** if `../ccya-<slug>` already exists. Mitigation: skill checks and either reuses or errors.
- **Branch naming collisions** if two efforts share the same slug. Mitigation: skill checks `git branch --list <slug>` before creating.
- **Agent loses track of which worktree it's in.** Mitigation: each skill starts with `pwd` + `git branch --show-current` verification.
- **PR creation fails** if `gh` is not authenticated. Mitigation: review-code checks `gh auth status` and errors gracefully.

## Status
`completed`

## Phases

3 phases: (1) cross-skill rules and config, (2) skill output formats and consolidation, (3) worktree+branch lifecycle and PR creation.

## Implementation — Phase 1: Cross-skill rules and config

### Context files to load
- `~/.config/opencode/AGENTS.md`
- `/Users/pwilson/Repos/ccya/AGENTS.md`

### Detailed steps

#### Step 1.1 — Add "stay in your lane" cross-skill rule

**File:** `~/.config/opencode/AGENTS.md`

**What:** Add a new cross-skill rule under the existing Cross-skill Rules section (after "Question markers" at line 59):

```
- **Stay in your lane.** Only touch files the plan or design explicitly names.
  Do not restore deleted files, revert prior work, or modify anything outside
  your stated scope without explicit user approval. If you discover something
  outside scope that needs fixing, flag it — do not fix it.
```

**Why:** Prevents agents from undoing intentional deletions or reverting prior work.

**Validation:** `grep -n "Stay in your lane" ~/.config/opencode/AGENTS.md` returns a match.

#### Step 1.2 — Add authority hierarchy decision

**File:** `~/.config/opencode/AGENTS.md`

**What:** Add a new section after "Cross-skill Rules" (after line 59) or as a new cross-skill rule:

```
- **Authority hierarchy.** Design doc > plan > source. Implementers treat the
  design doc as ground truth when source and plan conflict.
```

**Why:** Design captures final decisions. Plan inherits from design. Source is lowest authority.

**Validation:** `grep -n "Authority hierarchy" ~/.config/opencode/AGENTS.md` returns a match.

#### Step 1.3 — Update local ccya AGENTS.md skill descriptions

**File:** `/Users/pwilson/Repos/ccya/AGENTS.md`

**What:** Update the Skills section (lines 123-132):
- Remove `flesh-design` from the list
- Update `create-design` description to mention worktree/branch lifecycle
- Update `execute` description to mention worktree/branch lifecycle and commit prefix
- Update `review-design` description to mention single mode and output format
- Update `review-plan` description to mention enhanced chat output
- Update `review-code` description to mention PR creation

**Why:** Local AGENTS.md must reflect the new skill descriptions and workflow rules.

**Validation:** `grep -c "flesh-design" /Users/pwilson/Repos/ccya/AGENTS.md` returns 0.

#### Step 1.4 — Verify permission config is correct

**File:** `~/.config/opencode/opencode.jsonc`

**What:** Verify that `~/.config/opencode/*` is in external_directory allow list and `"*": "ask"` is set. No changes needed if already correct.

**Why:** Permission config was already fixed per design.

**Validation:** `grep -A2 "external_directory" ~/.config/opencode/opencode.jsonc` shows correct config.

## Implementation — Phase 2: Skill output formats and consolidation

### Context files to load
- `~/.config/opencode/skills/review-design/SKILL.md`
- `~/.config/opencode/skills/review-plan/SKILL.md`
- `~/.config/opencode/skills/review-code/SKILL.md`
- `~/.config/opencode/skills/plan/SKILL.md`
- `~/.config/opencode/skills/create-design.md/SKILL.md`
- `~/.config/opencode/skills/execute/SKILL.md`

### Detailed steps

#### Step 2.1 — Delete flesh-design skill

**File:** `~/.config/opencode/skills/flesh-design/SKILL.md`

**What:** Delete the entire flesh-design skill directory: `rm -rf ~/.config/opencode/skills/flesh-design/`

**Why:** flesh-design merged into review-design. No stub needed.

**Validation:** `ls ~/.config/opencode/skills/flesh-design/` returns "No such file or directory".

#### Step 2.2 — Update review-design skill

**File:** `~/.config/opencode/skills/review-design/SKILL.md`

**What:** Replace the entire file with the new single-mode version:
- Update description to mention single mode and output format
- Replace old review output format with new chat output (verdict + summary + key blockers) and file output (Key Blockers → Design Ambiguities → Suggested Improvements → Minor Notes)
- Add section definitions for each category
- Update "Done when" to match single mode
- Remove old severity-based report sections

**Why:** Consolidates flesh-design into review-design with a single mode.

**Validation:** `wc -l ~/.config/opencode/skills/review-design/SKILL.md` shows ~120 lines (reduced from 159).

#### Step 2.3 — Update review-plan skill

**File:** `~/.config/opencode/skills/review-plan/SKILL.md`

**What:** Update the review output format to include chat output:
- Add chat output section before the file output: verdict + one-para plan summary + blocks-execution items
- Keep existing file output format

**Why:** review-plan needs enhanced chat output per output format standards.

**Validation:** `grep -n "One-para plan summary" ~/.config/opencode/skills/review-plan/SKILL.md` returns a match.

#### Step 2.4 — Update plan skill

**File:** `~/.config/opencode/skills/plan/SKILL.md`

**What:** Add "Design Reference" field to the plan format. Insert it after "Purpose" (after line 48) as:

```
## Design Reference

Link to the source design doc: `docs/design/<slug>-design.md`
```

**Why:** Plans should reference their source design doc.

**Validation:** `grep -n "Design Reference" ~/.config/opencode/skills/plan/SKILL.md` returns a match.

#### Step 2.5 — Update create-design skill

**File:** `~/.config/opencode/skills/create-design.md/SKILL.md`

**What:** Update the "Done when" section to mention enhanced chat output. Add a "Chat output" instruction before "File placement":

```
## Chat output

After writing the design doc, output in chat:
- Key decisions and firm decisions
- Open questions that need user attention
- Blockers or ambiguities that need resolution
- Link to the design doc file path
```

**Why:** create-design needs enhanced chat output per output format standards.

**Validation:** `grep -n "Chat output" ~/.config/opencode/skills/create-design.md/SKILL.md` returns a match.

#### Step 2.6 — Update execute skill

**File:** `~/.config/opencode/skills/execute/SKILL.md`

**What:** Update the workflow section:
- Add brief phase output instruction: after each phase, output "X done, moving to Y" — elaborate only for blockers or deviations
- Update lint/typecheck instruction: run only at end of all phases, not per-fix
- Update "Done when" to remove test requirement (tests are temporarily removed)

**Why:** execute needs brief phase output and lint at end of all phases per design.

**Validation:** `grep -n "end of all phases" ~/.config/opencode/skills/execute/SKILL.md` returns a match.

#### Step 2.7 — Update review-code skill

**File:** `~/.config/opencode/skills/review-code/SKILL.md`

**What:** Update the review output format to include chat output:
- Add chat output section before the file output: verdict + fixes applied + findings needing user input
- Keep existing file output format

**Why:** review-code needs enhanced chat output per output format standards.

**Validation:** `grep -n "Verdict" ~/.config/opencode/skills/review-code/SKILL.md` returns a match.

#### Step 2.8 — Standardize question tool usage across all skills

**Files:** All skill files under `~/.config/opencode/skills/` (execute, plan, create-design, review-design, review-plan, review-code)

**What:** In every skill, replace or add clarification wherever the skill says "ask the user" or "ask using the question tool":
- Explicitly state: use the `question` tool (not freeform text)
- Always include a recommended option first in the multiple-choice answers
- Example phrasing: "ask using the `question` tool (recommended option first)"

Files to update:
- `~/.config/opencode/skills/execute/SKILL.md` — lines 20, 22
- `~/.config/opencode/skills/plan/SKILL.md` — lines 15, 25, 26
- `~/.config/opencode/skills/create-design.md/SKILL.md` — line 120
- `~/.config/opencode/skills/review-design/SKILL.md` — line 81
- `~/.config/opencode/skills/review-plan/SKILL.md` — lines 25, 73, 104
- `~/.config/opencode/skills/review-code/SKILL.md` — line 24

**Why:** Ensures consistent question-asking behavior across all skills. The `question` tool with a recommended option is the only valid way to ask questions.

**Validation:** `grep -rn "ask the user" ~/.config/opencode/skills/ | grep -v "question tool"` returns no matches.

## Implementation — Phase 3: Worktree+branch lifecycle and PR creation

### Context files to load
- `~/.config/opencode/skills/execute/SKILL.md`
- `~/.config/opencode/skills/create-design.md/SKILL.md`
- `~/.config/opencode/skills/review-code/SKILL.md`

### Detailed steps

#### Step 3.1 — Add worktree creation to execute skill

**File:** `~/.config/opencode/skills/execute/SKILL.md`

**What:** Add as the first step in the Workflow section (before "1. Load the plan"):

```
### 0. Verify/create worktree

Run `git branch --show-current` and `git rev-parse --show-toplevel`.
If on `main` with no worktree for the slug defined in the design doc,
create one:

```bash
git worktree add -b <slug> ../ccya-<slug> main
```

Then `cd ../ccya-<slug>` and verify with `git branch --show-current`.
If the slug is not found in the design doc, error and ask the user.
```

**Why:** Worktree is created during execute per design decision.

**Validation:** `grep -n "Verify/create worktree" ~/.config/opencode/skills/execute/SKILL.md` returns a match.

#### Step 3.2 — Add commit prefix convention to execute

**File:** `~/.config/opencode/skills/execute/SKILL.md`

**What:** Update the commit message format (step 5) to use `[<slug>]` prefix:

```bash
git add -A && git commit -m "[<slug>] <title>: <one-line summary>
```

**Why:** Commit messages use the slug prefix per design decision.

**Validation:** `grep -n "\[<slug>\]" ~/.config/opencode/skills/execute/SKILL.md` returns a match.

#### Step 3.3 — Add worktree creation to create-design

**File:** `~/.config/opencode/skills/create-design.md/SKILL.md`

**What:** Add step 0 before "Research phase":

```
### 0. Create worktree + branch

If the slug is defined in the design doc and we're on `main`, create
the worktree+branch:

```bash
git worktree add -b <slug> ../ccya-<slug> main
cd ../ccya-<slug>
```

If we're already on a feature branch, skip. Verify with
`git branch --show-current`.
```

**Why:** create-design may need to create the worktree if slug is set in design doc.

**Validation:** `grep -n "Create worktree" ~/.config/opencode/skills/create-design.md/SKILL.md` returns a match.

#### Step 3.4 — Add PR creation to review-code

**File:** `~/.config/opencode/skills/review-code/SKILL.md`

**What:** Add a new step after step 8 (after "Report findings"):

```
### 9. Create PR

After review passes, create a PR:

```bash
gh pr create --base main --title "<human-readable description>" \
  --body "Design: docs/design/<slug>-design.md
Plan: plans/<slug>-plan.md

<one-line summary of changes>"
```

Check `gh auth status` first. If not authenticated, error gracefully.
The review output should recommend: "Review complete. Ready to merge to main."
```

**Why:** PR creation creates the audit trail linking design → plan → code.

**Validation:** `grep -n "Create PR" ~/.config/opencode/skills/review-code/SKILL.md` returns a match.

#### Step 3.5 — Add worktree awareness to plan and review-plan

**File:** `~/.config/opencode/skills/plan/SKILL.md`

**What:** Add a brief worktree check in the Context loading section:

```
Run `git branch --show-current` to verify we're on the correct branch.
If on `main`, note it but proceed (plan lives on main per design).
```

**File:** `~/.config/opencode/skills/review-plan/SKILL.md`

**What:** Add a brief worktree check in the Context loading section:

```
Run `git branch --show-current` to verify we're on the correct branch.
```

**Why:** plan and review-plan need worktree awareness per design.

**Validation:** `grep -n "git branch --show-current" ~/.config/opencode/skills/plan/SKILL.md ~/.config/opencode/skills/review-plan/SKILL.md` returns matches in both.

### Tests to write or update

Tests are temporarily removed during refactor. No tests to write or update.
