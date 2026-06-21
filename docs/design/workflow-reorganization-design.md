# Workflow Reorganization

## Purpose

This document is the design authority for plans implementing the trunk-based development workflow across all ccya skills, AGENTS.md files, and the OpenCode permission config. It covers branch+worktree lifecycle, PR-based integration, skill consolidation, and the official "stay in your lane" and "fix all checks" rules.

## Problem Statement

The current workflow has no trunk-based discipline. All work lands directly on `main` with no feature branches, no PRs, and no audit trail linking design docs → plans → commits. Multiple skills (flesh-design, review-design) overlap in purpose with no clear boundary, and their output is not human-readable. There is no mechanism to prevent agents from touching files outside their planned scope, and preexisting lint/type errors are routinely left unfixed. The opencode permission config blocks agent access to skill files, preventing the agent from editing its own tools.

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
| Worktree per branch | `git worktree add -b <slug> ../ccya-<slug> main` at the start of design. All phases work inside that worktree. | Isolates work from parallel sessions. No switching branches in the main checkout. Git itself tracks worktrees in `.git/worktrees/`. |
| Worktree created by first skill that needs it | The create-design skill creates the worktree+branch as step 0. If no design phase is needed (e.g., a straightforward fix), execute creates it. | Avoids a dedicated init skill. The skill that begins the work owns the setup. |
| PR created at end of review-code | After code review passes, `gh pr create` with a body linking to the design doc and plan doc. PR title = human-readable branch slug. | Creates the audit trail. The PR body is the permanent record of what design and plan informed it. |
| Merge to main via PR | review-code skill suggests merging the PR. Human approves and merges. No auto-merge. | Keeps human in the loop for the integration decision. |
| flesh-design merged into review-design | Delete flesh-design skill. review-design absorbs its action-bias (fix what's unambiguous) and its "produce the full sharpened doc" output mode. | They validate the same things against source. The split between "fill gaps" (flesh) and "grill assumptions" (review) is artificial — every review finds gaps, every gap-fill requires scrutiny. |
| review-design gets two output modes | Mode A: structured report (as today) for a fresh design that needs thorough review. Mode B: full sharpened doc (from flesh-design) for close-to-final designs with only gaps to fill. | Covers both use cases without two skills. |
| "Stay in your lane" as cross-skill rule | A new cross-skill rule in global AGENTS.md: only touch files the plan/design explicitly names. Restore nothing. Revert nothing. If something outside scope needs fixing, flag it — don't fix it. | Prevents agents from undoing intentional deletions or reverting prior work. |
| "Fix all broken checks" as cross-skill rule | A new cross-skill rule: after any change, run lint + typecheck. If failures exist (including preexisting), fix them as part of this work. | Keeps the tree clean. Preexisting failures are not reasons to skip — they're reasons to fix. |
| Permission config fix | Add `~/.config/opencode/*` to external_directory allow list. Correct the typo `~/.config/.opencode/*`. | Unblocks agents from reading/writing their own skill files. |

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
- No mandate to fix preexisting lint/type errors.
- Permission config has a typo (`~/.config/.opencode/` instead of `~/.config/opencode/`) and a blanket deny that blocks agent access to skill files.

## Proposed Solution

### Core Changes

#### 1. Worktree + branch lifecycle (all skills)

Every body of work gets a git worktree and branch, created at the start of the first skill that touches it:

```bash
git worktree add -b <slug> ../ccya-<slug> main
```

The slug is the branch name, kebab-cased, e.g. `scene-state-separation`. From that point forward:
- Design doc lives at `docs/design/<slug>-design.md`
- Plan doc lives at `plans/<slug>-plan.md`
- Commit messages use `[<slug>]` prefix
- PR title uses the slug in human-readable form

All skills that write to the repo check `git branch --show-current` and `git rev-parse --show-toplevel` to determine which directory and branch they're on. If the branch is `main` and no slug is provided, the skill prompts or errors depending on phase.

#### 2. Skill changes

**create-design**: Add step 0: create worktree + branch. Write design doc inside worktree. Commit.

**flesh-design**: Deleted. Merged into review-design.

**review-design**: Absorbs flesh-design's action bias and output mode. Gets two output modes:
- Mode A (default for first review): Structured report with sections, severity levels — as today.
- Mode B (for close-to-final designs): Output the full sharpened design doc replacing the file, with a short summary of changes at the end.

**plan**: No structural change. Worktree-aware directory check. The plan doc is written on the feature branch.

**review-plan**: No structural change. Worktree-aware directory check.

**execute**: Step 0: verify correct branch/worktree. If on `main` with no worktree, create one or error. Add commit prefix convention `[<slug>]`. The lane rule and fix-checks rule are enforced here.

**review-code**: Add step after review passes: `gh pr create` with:
- Title: human-readable description (derived from branch slug)
- Body: links to `docs/design/<slug>-design.md` and `plans/<slug>-plan.md`, summary of changes
- Base: main
- The review output recommends: "Review complete. Ready to merge to main."

#### 3. Cross-skill rules (global AGENTS.md)

Two new rules under Cross-skill Rules:

```
- **Stay in your lane.** Only touch files the plan or design explicitly names.
  Do not restore deleted files, revert prior work, or modify anything outside
  your stated scope without explicit user approval. If you discover something
  outside scope that needs fixing, flag it — do not fix it.
```

```
- **Fix all broken checks.** After any change, run the project's lint and
  typecheck commands. If any failures exist (including preexisting ones),
  fix them as part of this change. A preexisting failure is not a reason
  to skip — fix it and move on.
```

#### 4. Output format simplification (review-design)

The review-design output format stays as-is for Mode A but gets a summary-first layout for human readers:

```
## Verdict
[tighten / question / sound]

## Summary
One paragraph.

## Must-fix (before plan)
- [FATAL/CRITICAL] items only

## Should-fix (before execute)
- [WARN] items

## FYI
- [MINOR] items

## Details
[Full structured report for LLM consumption]
```

#### 5. Permission config fix

Before any of this is usable, the global opencode config needs:
- `"~/.config/opencode/*": "allow"` (fix the dot typo from `~/.config/.opencode/*`)
- Either `"*": "ask"` (preferred) or `"*": "allow"` instead of `"*": "deny"` for external_directory

### Alternatives Considered and Rejected

- **Dedicated init-work skill:** Creates worktree+branch. Rejected because it adds an extra skill load for one mkdir-equivalent command. Cheaper to fold into create-design (step 0) and execute (step 0).
- **Keep flesh-design and review-design separate:** Rejected because the overlap is real and confusing. Both validate claims against source. Both fix what they can. The output format difference is not enough to justify two skills. A single skill with two output modes is cleaner.
- **Auto-merge PRs:** Rejected. The human should confirm the final integration.
- **Linear as master key:** Rejected per decision. Branch slug is the anchor. Linear ticket can appear in PR body as metadata if desired but is not required.

## Failure Modes and Risks

- **Worktree creation fails** if `../ccya-<slug>` already exists (leftover from a prior session). The skill must check and either reuse or error.
- **Branch naming collisions** if two efforts share the same slug. Mitigation: the skill checks `git branch --list <slug>` before creating.
- **Agent loses track of which worktree it's in.** Mitigation: each skill starts with `pwd` + `git branch --show-current` verification.
- **Flesh-design deletion breaks existing workflows** if someone loads the skill by name. Mitigation: create a stub skill file that says "This skill has been merged into review-design. Load review-design instead." Keep for one transition cycle.
- **PR creation fails** if `gh` is not authenticated. The review-code skill should check `gh auth status` and error gracefully.

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| flesh-design skill | `~/.config/opencode/skills/flesh-design/SKILL.md` | Merged into review-design |
| `"~/.config/.opencode/*"` (with dot) | `~/.config/opencode/opencode.json` | Typo, replaced with correct path |
| `"*": "deny"` on external_directory | `~/.config/opencode/opencode.json` | Replaced with `"*": "ask"` |

## What Is Unchanged

- ev skill — no changes
- customize-opencode skill — no changes
- lin skill — no changes (undecided, leave as-is)
- plan skill format — unchanged
- review-plan skill — minor: worktree awareness only
- review-code severity levels and checklist — unchanged
- Global AGENTS.md Cascade and Anti-tool Looping — unchanged
- Local ccya AGENTS.md content — will be updated to reflect new skill descriptions and workflow rules

## New Model Shapes

No new models. This is a workflow/skill config change only.

## Context for Implementing LLMs

- `~/.config/opencode/skills/execute/SKILL.md` — current execute skill, needs step 0 and commit prefix
- `~/.config/opencode/skills/create-design.md/SKILL.md` — current create-design, needs step 0
- `~/.config/opencode/skills/flesh-design/SKILL.md` — to be deleted (or replaced with redirect stub)
- `~/.config/opencode/skills/review-design/SKILL.md` — to absorb flesh-design modes and simplify output
- `~/.config/opencode/skills/review-code/SKILL.md` — needs PR creation step
- `~/.config/opencode/AGENTS.md` — needs two new cross-skill rules
- `~/.config/opencode/opencode.json` — needs permission fix
- `/Users/pwilson/Repos/ccya/AGENTS.md` — needs updated skill descriptions and workflow rules
