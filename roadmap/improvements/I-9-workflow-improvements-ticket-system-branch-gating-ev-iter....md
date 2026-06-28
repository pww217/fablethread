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

### 5. Iterative EV run (replaces standard 5-pack)

New `ev-run` workflow with phase-gated iteration:

**Phase 1: 1-5 turns — Critical/game-breaking issues**
- Run 5 scenarios, 1-5 turns each
- Threshold: critical failures, game-breaking bugs, obvious quality-degrading issues
- If no issues match this threshold, skip to Phase 2 without writing a report

**Phase 2: 10 turns — Intermediate issues**
- Run 5 scenarios, 10 turns each
- Threshold: intermediate degradations, pacing issues, extraction misses that matter
- If no issues match this threshold, skip to Phase 3 without writing a report

**Phase 3: 20-25 turns — Balance and long-term mechanics**
- Run 5 scenarios, 20-25 turns each
- Focus: balance, long-term mechanical assessment, nuanced issues
- Only runs when Phase 1 or 2 found issues, or when user explicitly requests full eval

**Output:**
- Each phase writes a brief phase report to `evals/runs/<group>/PHASE-N.md`
- Final consolidated report at `evals/runs/<group>/REPORT.md` only if issues were found
- If all phases skip, output: "No issues found at any threshold. Engine appears stable."

**Changes required:**

- Rewrite `ev-run/SKILL.md` with the iterative phase-gated workflow
- Update `AGENTS.md` EV section to reference the new workflow
- Update `docs/ev/` docs if needed

### 6. EV-review: targeted deep dive

New `ev-review` workflow focused on specific mechanics:

**Changes required:**

- Rewrite `ev-review/SKILL.md` to be a targeted deep dive:
  - User specifies which mechanic(s) to review (e.g., "pacing", "convergence", "ruling")
  - Run targeted checkers against relevant runs, not the full rubric
  - Focus on specific turn ranges relevant to the mechanic
  - Produce a focused report, not a full rubric pass
- Full rubric passes are now the job of `ev-run` (Phase 3), not `ev-review`
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
7. **Cross-linking in frontmatter + skills** — update schema, update all skills
8. **Iterative EV run** — rewrite ev-run skill
9. **Targeted EV-review** — rewrite ev-review skill

## Risks

- Retroactive labeling: need to ensure no duplicate ticket IDs across types (F, B, I, E are separate sequences, so this is fine)
- EV iteration: need to define clear thresholds for each phase to avoid ambiguity
- Cross-linking: existing design docs and plans don't have ticket references — they'll need to be updated as part of retroactive labeling or on next touch

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
- `ev-run`: Calls `ticket` skill to create new `E-` tickets for findings
- `ev-review`: Calls `ticket` skill to update validating items, create new tickets

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
