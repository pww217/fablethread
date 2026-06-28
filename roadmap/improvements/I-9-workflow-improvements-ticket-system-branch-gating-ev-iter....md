---
title: "Workflow improvements: ticket system, branch gating, EV iteration, cross-linking"
status: new
urgency: 2
size: large
created: 2026-06-27
ticket_id: I-9
labels:
  - tooling
  - workflow
---

## Problem

The current workflow has several friction points:

1. **Branch creation is automatic** — `execute` creates branches without asking. Most changes don't warrant a branch, but there's no threshold or gate.
2. **Plan skill sets design doc to "implemented"** — `plan/SKILL.md` line 27-28 sets the design doc status to `implemented`. This is the execute skill's job, not the plan skill's.
3. **EV runs are time-consuming** — The current 5-pack + 5-pack + 5-pack approach wastes time on stable engines. No phase-gating based on issue severity.
4. **EV-review is a full rubric pass** — Should be a targeted deep dive on specific mechanics, not a repeat of the full eval.
5. **No ticket numbering system** — Roadmap items use filename slugs only. No easy reference for commits, PRs, plans, designs, or cross-linking.
6. **No eval ticket type** — Eval findings don't fit cleanly into bugs or improvements. They're a hybrid: not clearly broken, but not quite right either.
7. **No cross-linking** — Design docs, plans, PRs, and tickets don't reference each other. There's no single source of truth that ties the lifecycle together.
8. **No ticket skill** — Creating/updating tickets is ad-hoc. No enforcement of frontmatter, status transitions, slug conventions, or type inference.

## Changes

### 1. Ticket ID system (F-, B-, I-, E-)

Add a ticket ID prefix to every roadmap item:

| Type | Prefix | Directory |
|------|--------|-----------|
| Feature | `F-1`, `F-2`, ... | `roadmap/features/` |
| Bug | `B-1`, `B-2`, ... | `roadmap/bugs/` |
| Improvement | `I-1`, `I-2`, ... | `roadmap/improvements/` |
| Eval | `E-1`, `E-2`, ... | `roadmap/evals/` (new) |

**Changes required:**

- Add `roadmap/evals/` directory for eval-derived tickets
- Add `E-` prefix type to `generate-roadmap.py`:
  - New `EVALS_DIR = ROADMAP_DIR / "evals"`
  - Add `eval` to `TYPE_ORDER`, `TYPE_EMOJIS`, `get_type()`
  - Add `evals` to `FILE_STATUS_MAP`
  - Auto-archive applies to evals too
- Add `ticket_id` field to frontmatter schema:
  ```yaml
  ticket_id: B-42
  ```
- Retroactively assign ticket IDs to all existing roadmap files
- Update `AGENTS.md` to reference ticket IDs in commit prefixes, PR titles, plan/design filenames
- Commit prefix becomes `[<slug>] [B-42]` or just `[B-42]` when slug is redundant

### 2. Branch creation: always ask first

**Changes required:**

- `execute/SKILL.md` step 0: Before creating a worktree/branch, ask the user:
  - "This plan touches N files across M modules. Do you want me to create a branch for this, or should I work on main?"
  - If the user says "no branch", execute on main with a descriptive commit
  - If the user says "branch", proceed as normal
- Document this in `AGENTS.md` under execution rules

### 3. Fix plan skill: remove "set design doc to implemented"

**Changes required:**

- `plan/SKILL.md` step 7: Remove the line that sets design doc status to `implemented`
- Design doc status should only be set to `implemented` by the `execute` skill after execution is complete
- This is a one-line removal

### 4. Execute skill: set design doc to implemented

**Changes required:**

- `execute/SKILL.md`: After successful execution (after step 4, before commit), set the design doc's YAML frontmatter status to `implemented`
- This is the correct place for this action — execution is what makes a design "implemented"

### 5. Iterative EV run — graduated scope, phase-gated, sequential

New `ev-run` workflow with graduated scope and clear phase thresholds. The eval is the AI's "track" — eval tickets serve as long-term memory across compactions, recording what's been done and what's next.

**Core principles:**
- **Graduated scope:** Start small, expand as stability increases. 1 game → 3 games → 5 games.
- **Sequential work:** One phase at a time. One issue at a time when investigating bugs. Do not pull multiple phases or issues into context simultaneously.
- **Eval tickets as memory:** Create ONE `E-` ticket per eval session (not per bug). Include eval group path, phase report links, and all findings in the ticket body. This ticket persists across compactions.
- **Phase 2 is the most important:** This is where nuanced bugs and regressions surface that Phase 1 misses and Phase 3 doesn't focus on. Invest effort here.

**Phase 1: 1 game, 5 turns — Critical/game-breaking bugs**
- Start with `noir-1930s:driven` (balanced pair). Run 5 turns.
- Threshold: critical failures, game-breaking bugs, obvious quality-degrading issues that make the game unplayable.
- If critical issues found: run 2-3 more pairs to confirm pattern, then STOP. Fix the bugs before continuing. Do not proceed to Phase 2 while critical bugs are unfixed — signals will be confounded.
- If no critical issues: skip to Phase 2.

**Phase 2: 3 games, 10-15 turns — Nuanced bugs and regressions**
- Run 3 persona pairs: `noir-1930s:driven`, `space-western:speedrunner`, `golden-piracy:completionist`.
- Threshold: intermediate degradations, pacing issues, extraction misses, mechanical inconsistencies that affect gameplay but don't break it.
- This is the primary investigation phase. Most actionable findings come from here.
- If bugs found that require a refactor (not a simple fix): STOP. Do not proceed to Phase 3. Fix the refactor first, then resume.
- If no intermediate issues: skip to Phase 3.
- If engine is still unstable: stay in Phase 2 until stable.

**Phase 3: 5 games, 20 turns — Balance, nuanced patterns, long-term mechanics**
- Run all 5 persona pairs: `noir-1930s:driven`, `space-western:speedrunner`, `golden-piracy:completionist`, `zombie-survival:cautious`, `allied-ww2:aggressive`.
- Only run when: critical bugs are fixed AND intermediate issues are resolved AND engine is stable.
- Focus: balance, long-term mechanical assessment, nuanced issues that need lots of evidence, edge cases in pacing/convergence/state management.
- This phase is skipped entirely if the engine is not yet stable.

**Phase gating thresholds:**
| Transition | Condition |
|------------|-----------|
| Phase 1 → Phase 2 | No critical bugs found, OR critical bugs fixed |
| Phase 2 → Phase 3 | No intermediate bugs found, OR intermediate bugs fixed, AND engine is stable |
| Skip Phase 3 | Critical bugs found that need refactor, OR intermediate bugs found that need refactor |
| Skip Phase 2 | User explicitly requests, OR Phase 1 found no critical issues and user wants intermediate check |

**Output:**
- Each phase writes findings to `evals/runs/<group>/PHASE-N.md`
- Final consolidated report at `evals/runs/<group>/REPORT.md`
- ONE `E-` ticket created per eval session with: eval group path, date, phase report links, all bugs/regressions, reproduction context, checker output
- The `E-` ticket serves as long-term memory — reference it on subsequent compactions

**Changes required:**

- Rewrite `ev-run/SKILL.md` with graduated scope, clear thresholds, sequential execution, eval ticket as memory
- Update `AGENTS.md` EV section to reference the new workflow
- Update `docs/ev/` docs if needed

### 6. EV-review: focused deep-dive, sequential, eval ticket memory

New `ev-review` workflow as a targeted deep dive on a specific mechanic, turn range, or fix validation. Not a full rubric pass — that's `ev-run`'s job.

**Core principles:**
- **Focused scope:** The user specifies what to examine (e.g., "convergence mechanic", "B-42 fix validation"). The skill delivers a customized report based on that request.
- **Sequential work:** One mechanic at a time. One issue at a time when investigating bugs. Do not pull multiple mechanics or issues into context simultaneously.
- **Eval tickets as memory:** If new issues warrant tracking, create ONE `E-` ticket per review session. The review report lives within the eval ticket, linking to the eval/save examined.
- **Read before analyzing:** Always read `docs/ev/COMMANDS.md`, `docs/ev/CHECKERS.md`, and relevant architectural docs from `docs/architecture/` for the mechanic being examined before running commands.

**What it does:**
- Examines a specific mechanic, turn range, or fix validation
- Runs targeted checkers and commands relevant to the request
- Produces a focused, customized report
- Links to the eval group or save that was examined

**What it does NOT do:**
- Full rubric pass (that's `ev-run`'s job)
- General engine review unless explicitly asked
- Analyze mechanics the user did not request

**Report location:** Lives within an `E-` ticket, linking to the eval/save examined. Not a standalone file.

**Changes required:**

- Rewrite `ev-review/SKILL.md` as a focused deep-dive:
  - User specifies what to examine; skill delivers customized report
  - Read COMMANDS.md, CHECKERS.md, and relevant arch docs before analyzing
  - Run only commands relevant to the request
  - Report lives within an eval ticket, links to the eval/save examined
  - ONE `E-` ticket per session if new issues warrant tracking
- Full rubric passes remain the job of `ev-run` (Phase 3), not `ev-review`
- `ev-review` is for: "I just changed the pacing system, does it still work?" not "how is everything doing?"

### 7. Cross-linking: tickets as source of truth

Every roadmap ticket becomes the central reference point. Design docs, plans, PRs, and commits all reference the ticket ID.

**Frontmatter schema additions:**

```yaml
---
title: "..."
status: new
urgency: 3
size: medium
created: 2026-06-27
ticket_id: B-42
design: docs/design/pacing-fix-design.md      # optional, added when design exists
plan: plans/pacing-fix-plan.md                 # optional, added when plan exists
pr:                                            # optional, added when PR is created
  url: https://github.com/.../pull/123
  branch: ccya-pacing-fix
labels:
  - engine
  - pacing
---
```

**Skill changes for cross-linking:**

- `create-design`: After creating design doc, update the roadmap file's `design` field with the path
- `plan`: After creating plan, update the roadmap file's `plan` field with the path
- `execute`: After creating branch/PR, update the roadmap file's `pr` field with URL and branch
- `review-plan`: Verify the plan references the correct ticket ID
- `review-code`: Verify the PR references the correct ticket ID in commit prefix and PR description

**AGENTS.md updates:**

- Document that all commits, PRs, plans, and designs should reference the ticket ID
- Commit format: `[<slug>] [B-42] <title>: <summary>`
- PR title: `B-42: <title>`
- Plan/design filenames: `<slug>-<ticket-id>-<name>.md` or just `<slug>-<name>.md` with ticket ID in frontmatter

### 8. Roadmap status lifecycle updates

Add `eval` type to the roadmap lifecycle:

**Evals:**
- `new` → `triaged` → `up-next` → `done` or `canceled`
- `triaged` = eval findings have been reviewed and categorized
- `up-next` = ready for investigation/fix

**Cross-reference in TOC:**
- `roadmap/backlog.md` includes eval items with `new`, `triaged` status
- `roadmap/active.md` includes eval items with `up-next` status

## Implementation order

1. **Ticket ID system + eval directory** — foundation for everything else
2. **Retroactive labeling** — assign IDs to all existing roadmap files
3. **Ticket skill** — enforce frontmatter, status transitions, slug conventions, type inference
4. **Branch gating in execute** — small change, high value
5. **Fix plan skill** — one-line removal
6. **Execute: set design to implemented** — one-line addition
7. **Execute: fix duplicate step and numbering** — remove duplicate "Load the plan" step, fix section numbering
8. **Create-design: fix file placement** — remove legacy `/plans/` fallback, standardize on `docs/design/`
9. **Cross-linking in frontmatter + skills** — update schema, update all skills
10. **Iterative EV run** — rewrite ev-run skill with graduated scope, thresholds, sequential execution, eval ticket as memory
11. **Targeted EV-review** — rewrite ev-review skill as focused deep-dive, sequential, eval ticket memory
12. **Review-code: review against design, not plan** — design doc is ground truth, verify every firm decision is faithfully realized

## Risks

- Retroactive labeling: need to ensure no duplicate ticket IDs across types (F, B, I, E are separate sequences, so this is fine)
- EV iteration: graduated scope requires clear thresholds to avoid ambiguity. Phase 2 is the critical investigation phase — most actionable findings come from there.
- Cross-linking: existing design docs and plans don't have ticket references — they'll need to be updated as part of retroactive labeling or on next touch
- Sequential execution: the AI tends to pull multiple phases/issues into context at once. Skills must explicitly enforce one-at-a-time execution for better results
- Eval tickets as memory: need to ensure the E- ticket format includes enough context for the AI to resume across compactions (eval group path, phase reports, what was done, what's next)

### 9. New `ticket` skill

A dedicated skill for creating, managing, and validating roadmap tickets. Loads when the user asks to create, update, or audit a roadmap item.

**Responsibilities:**

- **Create tickets:** Enforce frontmatter schema, assign ticket IDs, generate slugs, place in correct directory, run `make roadmap`
- **Update tickets:** Validate status transitions against lifecycle rules, update cross-link fields (`design`, `plan`, `pr`), update status/urgency/labels
- **Audit tickets:** Check for missing frontmatter, invalid status transitions, orphaned cross-references (e.g., design points to non-existent file), stale ticket IDs
- **Slug generation:** Enforce naming conventions (kebab-case, descriptive, no special chars)
- **Type inference:** Help user pick the right type (bug vs feature vs improvement vs eval) when ambiguous

**Frontmatter enforcement:**

Every ticket must have:
```yaml
---
title: "..."
status: <valid-status>
urgency: 1|2|3|4
size: small|medium|large|xlarge
created: YYYY-MM-DD
ticket_id: <TYPE>-<N>
design: <optional path>
plan: <optional path>
pr:
  url: <optional URL>
  branch: <optional branch>
labels:
  - <labels>
---
```

**Status transition validation:**

Enforce lifecycle rules:
- Bugs: `new` → `validated` → `up-next` → `testing` → `done`/`canceled`
- Features: `idea` → `scoping` → `up-next` → `done`/`canceled`
- Improvements: `idea` → `scoping` → `up-next` → `done`/`canceled`
- Evals: `new` → `triaged` → `up-next` → `done`/`canceled`

Reject invalid transitions with a clear error. Allow `canceled` from any status.

**Integration with other skills:**

- `create-design`: Calls `ticket` skill to create/update the roadmap file, then writes the design doc
- `plan`: Calls `ticket` skill to update `plan` field on roadmap file, sets status to `up-next`
- `execute`: Calls `ticket` skill to update `pr` field, sets design status to `implemented`, sets ticket status to `done` on completion
- `review-plan`: Calls `ticket` skill to verify plan references correct ticket
- `review-code`: Calls `ticket` skill to verify PR references correct ticket
- `ev-run`: Calls `ticket` skill to create ONE `E-` ticket per eval session, include eval group path, phase report links, and all findings
- `ev-review`: Calls `ticket` skill to update testing items, create ONE `E-` ticket per session if new issues warrant tracking, report lives within the eval ticket

**Skill definition:**

```yaml
---
name: ticket
description: Create, update, validate, and audit roadmap tickets with enforced standards
---
```

Lives in `.opencode/skills/ticket/SKILL.md`.

## Not in scope

- Changing the roadmap generation script's table format (keep as-is, just add ticket_id column)
- Changing the auto-archive logic (evals use same archive rules as bugs/features)
- Adding new checker types (out of scope for this ticket)
