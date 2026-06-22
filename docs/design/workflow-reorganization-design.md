# Workflow Reorganization

## Purpose

This document is the design authority for plans implementing the trunk-based development workflow across all ccya skills, AGENTS.md files, and the OpenCode permission config. It covers branch+worktree lifecycle, PR-based integration, skill consolidation, and output format standards.

## Problem Statement

The current workflow has no trunk-based discipline. All work lands directly on `main` with no feature branches, no PRs, and no audit trail linking design docs → plans → commits. Multiple skills (flesh-design, review-design) overlap in purpose with no clear boundary, and their output is not human-readable. There is no mechanism to prevent agents from touching files outside their planned scope.

## Constraints

- **Only one constraint:** The agent works in a single working directory per session. Worktrees must be created and entered into deliberately.

## Non-goals

- Does not change the ev or customize-opencode skills.
- Does not remove the lin skill (undecided).
- Does not change the content or structure of CCYA pipeline code — only the workflow around it.
- Does not retroactively convert existing work to branches.

## Decision Table

| Decision | What | Why |
|---|---|---|
| Branch slug is canonical key | Every body of work gets one branch. The branch name is the slug used in design doc filenames, plan doc filenames, commit prefixes, and PR title. No separate ticket ID or Linear key as master anchor. | Simplifies traceability — one name flows through the entire lifecycle. Drop dependency on Linear as mandatory marker. |
| Slug set in design doc | The slug is defined in the design doc. The worktree+branch is created during execute (after plan), not during create-design. | Design and plan live on main. Execution happens on the feature branch. One source of truth for the slug. |
| Worktree per branch | `git worktree add -b <slug> ../ccya-<slug> main` at the start of execute. All phases work inside that worktree. | Isolates work from parallel sessions. No switching branches in the main checkout. Git itself tracks worktrees in `.git/worktrees/`. |
| Worktree cleanup after PR merge | Worktree persists until the PR is merged to main, then removed. | Keeps it available for post-merge fixes if needed. |
| PR created at end of review-code | After code review passes, `gh pr create` with a body linking to the design doc and plan doc. PR title = human-readable branch slug. | Creates the audit trail. The PR body is the permanent record of what design and plan informed it. |
| Merge to main via PR | review-code skill suggests merging the PR. Human approves and merges. No auto-merge. | Keeps human in the loop for the integration decision. |
| flesh-design deleted | Delete flesh-design skill. review-design absorbs its action-bias and output mode into a single mode. | They validate the same things against source. The split between "fill gaps" (flesh) and "grill assumptions" (review) is artificial — every review finds gaps, every gap-fill requires scrutiny. |
| review-design single mode | One mode: update and refine the existing design doc, surfacing key blockers, design ambiguities, and suggested improvements. | Design is the creative/iterative phase. One mode is sufficient. |
| "Stay in your lane" as cross-skill rule | A new cross-skill rule in global AGENTS.md: only touch files the plan/design explicitly names. Restore nothing. Revert nothing. If something outside scope needs fixing, flag it — don't fix it. | Prevents agents from undoing intentional deletions or reverting prior work. |
| Authority hierarchy | Design doc > plan > source. Implementers treat the design doc as ground truth when source and plan conflict. | Design captures final decisions. Plan inherits from design. Source is lowest authority. |
| Lint/typecheck at end of all phases | Run lint + typecheck only at the end of all phases, not per-fix. | Reduces token waste. Aligns with AGENTS.md's "do not waste tokens on incremental check runs." |
| Question tool with recommendation | Any skill that asks questions must use the `question` tool with a recommended option first. Never ask open-ended questions. | Ensures the user can accept the default without thinking. Consistent across all skills. |

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
- flesh-design and review-design share ~80% of their work (both validate claims against source, both fix what they can, both flag what they can't). The only real difference is output format (full document rewrite vs structured report).
- review-design's output format is thorough but not human-readable for quick scanning. 13 required sections with [FATAL]/[CRITICAL]/[WARN] severity is correct for an LLM consuming it but too much for a person.
- No cross-skill protection against scope creep — agents can and do touch files outside their plan.

## Proposed Solution

### Core Changes

#### 1. Worktree + branch lifecycle

The slug is defined in the design doc. During execute (after plan), the worktree+branch is created:

```bash
git worktree add -b <slug> ../ccya-<slug> main
```

The slug is the branch name, kebab-cased, e.g. `scene-state-separation`. From that point forward:
- Design doc lives at `docs/design/<slug>-design.md` (on main)
- Plan doc lives at `plans/<slug>-plan.md` (on feature branch, moved to completed/ after merge)
- Commit messages use `[<slug>]` prefix
- PR title uses the slug in human-readable form

All skills that write to the repo check `git branch --show-current` and `git rev-parse --show-toplevel` to determine which directory and branch they're on. If the branch is `main` and no slug is provided, the skill errors.

#### 2. Skill changes

**create-design**: Add step 0: create worktree + branch if slug is not yet set. Write design doc inside worktree. Commit.

**flesh-design**: Deleted. No stub.

**review-design**: Single mode. Updates and refines the existing design doc, surfacing key blockers, design ambiguities, and suggested improvements. Output restructured:

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

Chat output: verdict + one-paragraph summary + key blockers.

**plan**: Add "Design Reference" field to plan format. Worktree-aware directory check. The plan doc is written on the feature branch.

**review-plan**: Chat output: one-paragraph plan summary + verdict + blocks-execution items. Worktree-aware directory check.

**execute**: Step 0: verify correct branch/worktree. If on `main` with no worktree, create one or error. Add commit prefix convention `[<slug>]`. Brief phase output ("X done, moving to Y"). Elaborate only for blockers or deviations. Lint/typecheck only at end of all phases.

**review-code**: Add step after review passes: `gh pr create` with:
- Title: human-readable description (derived from branch slug)
- Body: links to `docs/design/<slug>-design.md` and `plans/<slug>-plan.md`, summary of changes
- Base: main
- The review output recommends: "Review complete. Ready to merge to main."

#### 3. Cross-skill rules (global AGENTS.md)

One new rule under Cross-skill Rules:

```
- **Stay in your lane.** Only touch files the plan or design explicitly names.
  Do not restore deleted files, revert prior work, or modify anything outside
  your stated scope without explicit user approval. If you discover something
  outside scope that needs fixing, flag it — do not fix it.
```

#### 4. Output format standards

Every skill follows a consistent chat output pattern:

| Skill | Chat output | File output |
|---|---|---|
| create-design | Key decisions, firm decisions, open questions, blockers, ambiguities | Full design doc |
| review-design | Verdict, one-para summary, key blockers | Restructured doc (Key Blockers → Ambiguities → Improvements → Notes) |
| review-plan | One-para plan summary, verdict, blocks-execution items | Full report |
| review-code | Verdict, fixes applied, findings needing user input | Full diff review |
| plan | Design doc reference, phase summary | Full plan |
| execute | Brief phase completions, elaborate only for blockers | Commit message, plan status |

#### 5. Permission config

Already fixed. `~/.config/opencode/*` is in external_directory allow list. `"*": "ask"` is set for external_directory.

### Alternatives Considered and Rejected

- **Dedicated init-work skill:** Creates worktree+branch. Rejected because it adds an extra skill load for one mkdir-equivalent command. Cheaper to fold into create-design (step 0) and execute (step 0).
- **Keep flesh-design and review-design separate:** Rejected because the overlap is real and confusing. Both validate claims against source. Both fix what they can. One skill with one mode is cleaner.
- **Auto-merge PRs:** Rejected. The human should confirm the final integration.
- **Linear as master key:** Rejected per decision. Branch slug is the anchor. Linear ticket can appear in PR body as metadata if desired but is not required.
- **Fix all broken checks as cross-skill rule:** Rejected. Causes conflict with "stay in your lane" when lint errors exist outside plan scope. Scope explosion risk.

## Failure Modes and Risks

- **Worktree creation fails** if `../ccya-<slug>` already exists (leftover from a prior session). The skill must check and either reuse or error.
- **Branch naming collisions** if two efforts share the same slug. Mitigation: the skill checks `git branch --list <slug>` before creating.
- **Agent loses track of which worktree it's in.** Mitigation: each skill starts with `pwd` + `git branch --show-current` verification.
- **PR creation fails** if `gh` is not authenticated. The review-code skill should check `gh auth status` and error gracefully.

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| flesh-design skill | `~/.config/opencode/skills/flesh-design/SKILL.md` | Deleted. No stub. |

## What Is Unchanged

- ev skill — no changes
- customize-opencode skill — no changes
- lin skill — no changes (undecided, leave as-is)
- review-code severity levels and checklist — unchanged
- Global AGENTS.md Cascade and Anti-tool Looping — unchanged
- Local ccya AGENTS.md content — will be updated to reflect new skill descriptions and workflow rules

## New Model Shapes

No new models. This is a workflow/skill config change only.

## Context for Implementing LLMs

- `~/.config/opencode/skills/execute/SKILL.md` — current execute skill, needs step 0, commit prefix, brief phase output, lint at end of all phases
- `~/.config/opencode/skills/create-design.md/SKILL.md` — current create-design, needs step 0, enhanced chat output
- `~/.config/opencode/skills/flesh-design/SKILL.md` — to be deleted
- `~/.config/opencode/skills/review-design/SKILL.md` — single mode, restructured output, enhanced chat output
- `~/.config/opencode/skills/review-code/SKILL.md` — needs PR creation step
- `~/.config/opencode/skills/review-plan/SKILL.md` — enhanced chat output with plan summary
- `~/.config/opencode/skills/plan/SKILL.md` — add "Design Reference" field to plan format
- `~/.config/opencode/AGENTS.md` — needs "stay in your lane" cross-skill rule, authority hierarchy decision
- `/Users/pwilson/Repos/ccya/AGENTS.md` — needs updated skill descriptions and workflow rules
