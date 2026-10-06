---
status: reviewed
created: 2026-06-21
---

# Workflow Reorganization

## Purpose

This document is the design authority for plans implementing the trunk-based development workflow across all ccya skills, AGENTS.md files, and the OpenCode permission config. It covers branch+worktree lifecycle, PR-based integration, in-repo planning system, skill consolidation, parallel agent safety, output format standards, and cross-skill behavioral rules.

## Problem Statement

The current workflow has no trunk-based discipline. All work lands directly on `main` with no feature branches, no PRs, and no audit trail linking roadmap entries → design docs → plans → commits. Multiple skills (flesh-design, review-design) overlap in purpose with no clear boundary. Agents routinely touch files outside their planned scope, revert other agents' work, and leave preexisting lint/type errors unfixed. Planning is scattered across Linear (inaccessible to agents) and ad-hoc markdown. There is no mechanism to discover what work is in flight, queued, or completed without asking.

## Constraints

- The agent works in a single working directory per session. Worktrees must be created and entered into deliberately.
- The planning system must be agent-readable and agent-writable. No external tools.

## Non-goals

- Does not change the ev or customize-opencode skills.
- Does not remove the lin skill yet (undecided). It becomes secondary — roadmap files are the primary system.
- Does not change the content or structure of CCYA pipeline code — only the workflow around it.
- Does not retroactively convert existing work to branches.

## Decision Table

| Decision | What | Why |
|---|---|---|
| Branch slug is canonical key | Every body of work gets one branch. The branch name is the slug used in roadmap filename, design doc filename, plan doc filename, commit prefixes, and PR title. No separate ticket ID required. | Simplifies traceability — one name flows through the entire lifecycle. |
| Worktree created at start of design | `git worktree add -b <slug> ../ccya-<slug> main` at the start of create-design. All phases (design, plan, execute) share this worktree. Design doc, plan doc, and code all live on the same branch. | Isolates work from parallel sessions. Git tracks worktrees in `.git/worktrees/`. Slug is defined at the earliest point and flows through everything. |
| PR created at end of review-code | After code review passes, `gh pr create` with a body linking to the roadmap entry, design doc, and plan doc. PR title = human-readable branch slug. | Creates the audit trail. The PR body is the permanent record of what planning and design informed the code. |
| Merge to main via PR | review-code skill suggests merging the PR. Human approves and merges. No auto-merge. | Keeps human in the loop for the integration decision. |
| flesh-design merged into review-design | Delete flesh-design skill. review-design absorbs its action-bias into a single output mode. | They validate the same things against source. The split is artificial. |
| review-design single mode | Single mode: update and refine the existing design doc, surfacing key blockers, design ambiguities, and suggested improvements. No separate "report" vs "sharpen" modes. | One mode is sufficient. The output goes both to the file (restructured sections) and to chat (verdict + summary + blockers). |
| In-repo planning system | `roadmap/` directory with individual MD files for bugs and features. Status in YAML frontmatter, not directory paths. Auto-generated `roadmap/backlog.md`, `roadmap/active.md`, `roadmap/done.md`. Slug-based status values: bugs (new, validated, up-next, testing, done, canceled), features (idea, scoping, up-next, done, canceled). | Agent-readable, agent-writable. Slug ties roadmap entry → design → plan → branch → PR. |
| Status in file, not in path | Status is a frontmatter field. Files stay in `bugs/` or `features/` regardless of status. Completed items move to `archive/`. | Moving files between directories per status change is friction. A field update is one edit. |
| Planning lifecycle tied to skills | Skills update roadmap status spontaneously at each phase transition (scoping → validated → up-next → testing → done for bugs; scoping → up-next → done for features). Design docs update their own status (scoping → reviewed → implemented). | Self-tracking. No separate status-update workflow. |
| "Stay in your lane" as cross-skill rule | Only touch files the plan or design explicitly names. Do not restore deleted files, revert prior work, or modify anything outside your stated scope. | Prevents agents from undoing intentional deletions or reverting other agents' work. |
| "Assume parallel work" as cross-skill rule | Assume other agents work concurrently. Never revert code you didn't write. Investigate via `git log`, `git diff`, `git status`. If you don't understand a change, ask the user — do not act. | Prevents the primary failure mode: one agent reverting another's commits. |
| Authority hierarchy | Design doc > plan > source. Implementers treat the design doc as ground truth when source and plan conflict. | Design captures final decisions. Plan inherits from design. |
| Lint/typecheck at end of all phases | Run lint + typecheck once after all phases complete, not per-phase. | Reduces token waste. Aligns with existing AGENTS.md convention. |
| Question tool with recommendation | Any skill that asks questions must use the `question` tool with a recommended option first. Never ask open-ended questions. | Ensures user can accept the default without thinking. Consistent across all skills. |
| Chat output per skill | Every skill outputs a brief chat summary: verdict, key findings, what changed. No verbose prose. File output contains full detail. | Human reads chat output to understand what happened without reading the full file diff. |

## Open Questions

None. All resolved.

## Current State — What Exists

### Skill inventory

| Skill | Lines | Purpose |
|---|---|---|
| execute | 90 | Execute plan step by step. Commit to current branch. |
| plan | 136 | Write plan doc from design doc. |
| create-design | 141 | Write design doc. |
| flesh-design | 57 | Validate & sharpen design doc against source. Fix gaps. |
| review-design | 159 | Grill design doc against source. Produce structured report. |
| review-plan | 108 | Review plan doc against source. |
| review-code | 99 | Review diff/PR. No PR creation step. |
| ev | 26 | Inspect turn data. CCYA-specific. |
| lin | 33 | Linear ticket management. |

### Problems with Current State

- No branch discipline — all work lands on main.
- No PR creation — no audit trail linking design → plan → code.
- flesh-design and review-design share ~80% of their work. Output is not human-readable.
- No cross-skill protection against scope creep — agents revert other agents' work.
- Planning system (Linear) is external, not agent-accessible.
- No way to discover what work exists, its status, or its priority without asking.
- Existing `lin` skill is complex for a one-person project and generates context that spreads everywhere.
- `roadmap/` directory does not exist. No planning files exist in the repo.
- ~60 existing Linear tickets have no in-repo representation.

## Proposed Solution

### Core Changes

#### 1. Worktree + branch lifecycle

Every body of work gets a git worktree and branch, created at the start of create-design:

```bash
git worktree add -b <slug> ../ccya-<slug> main
```

The slug is the branch name, kebab-cased, e.g. `scene-state-separation`. From that point forward all work (design doc, plan doc, code) lives on this branch in the worktree. When the PR merges to main, the worktree can be removed.

If no design phase is needed (e.g., a straightforward bugfix), execute creates the worktree+branch as its step 0 instead.

#### 2. In-repo planning system

Replace Linear as the primary planning system with a `roadmap/` directory in the repo root.

##### Directory structure

```
roadmap/
  bugs/
    bug-descriptive-slug.md
    bug-another-bug.md
  features/
    feature-descriptive-slug.md
    improvement-better-prompts.md
    moonshot-narrative-graph.md
  archive/
    (completed or canceled items)
  index.md        (auto-generated by scripts/generate-roadmap.py)
```

##### File format (frontmatter)

```yaml
---
title: <human-readable title>
status: new                # Bugs: new | validated | up-next | testing | done | canceled
                           # Features: idea | scoping | up-next | done | canceled
urgency: 3                 # 1=urgent | 2=high | 3=medium | 4=low
size: small               # small | medium | large | xlarge
created: 2026-06-21        # date added
completed:                 # date completed (blank until done)
labels: []                 # e.g. ["ui", "prompt", "scene", "infra", "balancing", "improvement", "moonshot"]
design:                    # path to design doc, if one exists (blank until created)
plan:                      # path to plan doc, if one exists (blank until created)
---
```

Design docs use a separate status lifecycle:
```yaml
---
status: scoping
created: YYYY-MM-DD
---
```
- `scoping` → `reviewed` → `implemented`
- Set by: create-design (scoping), review-design (reviewed), plan (implemented)

Labels cover categories that aren't types: `improvement` and `moonshot` are labels on a `feature` type item, refining scale/scope rather than separate top-level types.

##### Auto-generated index

A Python script `scripts/generate-roadmap.py`:
- Scans `roadmap/bugs/`, `roadmap/features/`, `roadmap/archive/`
- Parses YAML frontmatter from each MD file
- Groups items by status
- Writes `roadmap/backlog.md`, `roadmap/active.md`, `roadmap/done.md` with sections:
  - **Queued** (up-next)
  - **Validating** (validated)
  - **Done** (done)
  - **Canceled** (canceled)
- Each item shows: title (from frontmatter), urgency, size, labels, created date, linked design/plan paths
- Archived items listed in a separate section at the bottom

Wired as a make target (`make roadmap`). The index is informational only — the source files are authoritative.

##### Lifecycle integration with skills

| Phase | Skill | Roadmap action |
|---|---|---|
| New idea/bug surfaces | (manual or ad-hoc) | Create `roadmap/bugs/<slug>.md` or `roadmap/features/<slug>.md` with status `new` or `idea` |
| Design begins | create-design | Create or update roadmap file with status `scoping` |
| Bug validated | bug-triage | Update status: `new` → `validated` |
| Design reviewed | review-design | Update status: approved → `up-next`, rejected → `canceled` |
| Work begins | execute | Update status: `validated` → `up-next` (bugs) or already `up-next` (features) |
| PR merged | (human) | Update status to `testing` (bugs with eval needed) or `done`, set `completed` date, move file to `roadmap/archive/` |
| Eval passes | ev-review | Update status to `done`, set `completed` date, move file to `roadmap/archive/` |

The roadmap self-tracks. Status updates happen spontaneously as the skill does its work — no separate step.

##### Slug chain

```
roadmap/features/feature-scene-state-separation.md
    ↓ (shared slug)
docs/design/scene-state-separation-design.md
    ↓
plans/scene-state-separation-plan.md
    ↓ (git worktree add -b)
branch: scene-state-separation
    ↓ (commit -m "[scene-state-separation] ...")
commits
    ↓ (gh pr create --title "...")
PR body: links to roadmap entry, design doc, plan doc
    ↓
merge to main
```

#### 3. Skill changes

**create-design**:
- Step 0: create worktree + branch (`git worktree add -b <slug> ../ccya-<slug> main`).
- Create or update roadmap file with status `scoping`.
- Write design doc at `docs/design/<slug>-design.md` with YAML frontmatter: `status: scoping`, `created: YYYY-MM-DD`.
- Chat output: key decisions, firm decisions, open questions, blockers, ambiguities.

**flesh-design**: Deleted. No stub.

**review-design**: Single mode. Updates and refines the existing design doc. Restructured sections in the file:

```
## Key Blockers
- Things that will break if plan is written as-is.

## Design Ambiguities
- Things the plan author will have to guess at.

## Suggested Improvements
- Things that would make the design better but aren't required.

## Minor Notes
- Style, clarity, or completeness suggestions with no behavioral consequence.
```

Chat output: verdict + one-paragraph summary + key blockers. Update roadmap status (approved → `up-next`, rejected → `canceled`). Update design doc status to `reviewed`.

**plan**:
- Read design doc from the worktree.
- Write plan doc at `plans/<slug>-plan.md`.
- Add "Design Reference" field to plan format linking back to the design doc.
- Chat output: design doc reference + phase summary.
- Update roadmap status to `up-next` (if not already set).
- Update design doc status to `implemented`.

**review-plan**:
- Chat output: one-paragraph plan summary + verdict + blocks-execution items.
- Worktree-aware directory check.

**execute**:
- Step 0: verify correct branch/worktree. If on `main` with no worktree, create one (`git worktree add -b <slug> ../ccya-<slug> main`).
- Commit prefix convention `[<slug>]`.
- Brief phase output ("X done, moving to Y"). Elaborate only for blockers or deviations.
- Lint + typecheck at end of ALL phases, not per-phase.
- Move plan from `plans/<slug>-plan.md` to `plans/completed/<bucket>/` (most appropriate existing bucket subfolder) on the branch.

**review-code**:
- Add step after review passes: `gh pr create` with:
  - Title: human-readable description (derived from branch slug)
  - Body: links to roadmap entry, design doc, plan doc.
  - Base: main
- The review output recommends: "Review complete. Ready to merge to main."

#### 4. Cross-skill rules (global AGENTS.md)

Three new rules under Cross-skill Rules:

```
- **Stay in your lane.** Only touch files the plan or design explicitly names.
  Do not restore deleted files, revert prior work, or modify anything outside
  your stated scope without explicit user approval. If you discover something
  outside scope that needs fixing, flag it — do not fix it.
```

```
- **Assume parallel work.** Other agents may be working in this repo
  concurrently. Never revert code, delete files, or undo changes you did not
  make and do not have context for. If you encounter modified files, unstaged
  changes, or recent commits outside your scope, investigate:
  `git log --oneline -5`, `git diff`, `git status`. If you still cannot
  understand why a change exists or it blocks your work, ask the user using
  the `question` tool — do not act on assumptions.
```

#### 5. Output format standards

Every skill follows a consistent chat output pattern:

| Skill | Chat output | File output |
|---|---|---|
| create-design | Key decisions, firm decisions, open questions, blockers, ambiguities | Full design doc |
| review-design | Verdict, one-para summary, key blockers | Restructured doc (Key Blockers → Ambiguities → Improvements → Notes) |
| plan | Design doc reference, phase summary | Full plan |
| review-plan | One-para plan summary, verdict, blocks-execution items | Full report |
| execute | Brief phase completions, elaborate only for blockers | Commit message, plan status update |
| review-code | Verdict, fixes applied, findings needing user input | Full diff review |

#### 6. Permission config

Already fixed. `~/.config/opencode/*` is on the external_directory allow list. `"*": "ask"` is set for external_directory.

### Alternatives Considered and Rejected

- **Dedicated init-work skill:** Creates worktree+branch. Rejected because it adds an extra skill load for one `git worktree add` command. Cheaper to fold into create-design (step 0) and execute (step 0).
- **Keep flesh-design and review-design separate:** Rejected because the overlap is real and confusing. Both validate claims against source. One skill with one mode is cleaner.
- **Auto-merge PRs:** Rejected. The human should confirm the final integration.
- **Status in directory paths** (`bugs/new/`, `bugs/in-progress/`): Rejected. Moving files between directories per status change is friction compared to editing a frontmatter field. Breaks permalinks.
- **Single roadmap.md file:** Rejected. Individual files support parallel editing, clearer git history per item, and simpler status changes (edit one field vs. editing a section of a large file).
- **GitHub Issues as primary tracker:** Rejected. User preference to keep planning in-repo and locally accessible.
- **Worktree created during execute only:** Rejected after discussion. If design and plan live on main, the branch slug is defined late, and design/plan edits on main can conflict with parallel work. Creating the worktree at design time keeps everything on the feature branch from the start.

## Failure Modes and Risks

- **Worktree creation fails** if `../ccya-<slug>` already exists (leftover from a prior session). The skill must check and either reuse or error.
- **Branch naming collisions** if two efforts share the same slug. Mitigation: the skill checks `git branch --list <slug>` before creating.
- **Agent loses track of which worktree it's in.** Mitigation: each skill starts with `pwd` + `git branch --show-current` verification.
- **Flesh-design deletion breaks existing workflows** if someone loads the skill by name. Mitigation: skill file deleted, no stub.
- **PR creation fails** if `gh` is not authenticated. The review-code skill should check `gh auth status` and error gracefully.
- **Auto-generator and roadmap files drift** if the script isn't run. Mitigation: the index is informational only. Source files are authoritative.

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| flesh-design skill | `~/.config/opencode/skills/flesh-design/SKILL.md` | Deleted (merged into review-design) |
| lin skill as primary planning | `~/.config/opencode/skills/lin/SKILL.md` | Defunct. Replaced by roadmap/ files. |

## What Is Unchanged

- ev skill — no changes
- customize-opencode skill — no changes
- review-code severity levels and checklist — unchanged
- Global AGENTS.md Cascade and Anti-tool Looping — unchanged
- Local ccya AGENTS.md content — will be updated (skill descriptions, workflow rules, roadmap conventions)
- The auto-generated `roadmap/backlog.md`, `roadmap/active.md`, `roadmap/done.md` — informational only, never the source of truth

## New Model Shapes

No new models. This is a workflow/skill config change only.

## Context for Implementing LLMs

- `~/.config/opencode/skills/execute/SKILL.md` — needs step 0, commit prefix, lint at end
- `~/.config/opencode/skills/create-design.md/SKILL.md` — needs step 0 (worktree), roadmap file creation, design doc frontmatter, enhanced chat output
- `~/.config/opencode/skills/review-design/SKILL.md` — single mode, restructured output, roadmap status update, design doc status update
- `~/.config/opencode/skills/plan/SKILL.md` — add "Design Reference" field, roadmap status update, design doc status update
- `~/.config/opencode/skills/review-plan/SKILL.md` — enhanced chat output with plan summary
- `~/.config/opencode/skills/review-code/SKILL.md` — needs PR creation step, roadmap status update
- `~/.config/opencode/AGENTS.md` — needs two new cross-skill rules (stay in your lane, assume parallel work), authority hierarchy
- `AGENTS.md` — needs updated skill descriptions, workflow rules, roadmap conventions
- `scripts/generate-roadmap.py` — new file, auto-generates roadmap index
- `Makefile` — add `roadmap` target
- `roadmap/` directory — new, contains all planning files