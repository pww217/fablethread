---
title: Standardize PR descriptions with a common template
status: scoping
urgency: 3
size: small
created: 2026-06-27
ticket_id: I-6
labels:
  - process
  - docs
---

## Problem

PR descriptions on this repo are inconsistent across all 8 merged/open PRs. Reviewing them surfaces four axes of drift:

**Title format** — no convention. Mix of:
- `[<slug>]` prefix: #5, #6
- Conventional prefix: `chore:` (#2), `Design:` (#1)
- Bare titles: #3, #4, #7, #8

**Header link block** — only #3, #4, #5, #6, #7 include a `## Design` / `## Plan` / `## Roadmap` link block at the top. #1, #2, #8 omit it entirely, so reviewers have to grep the branch for the source of truth.

**Body structure** — every PR invents its own. Examples:
- Phase-numbered bullets (#8)
- Issue → fix list (#7)
- Commit-by-commit recap (#4)
- Subsections `Contracts touched / Tests / Docs / Rollback risk` (#1)
- Single `## Summary` paragraph (#3, #5)

**Verification + risk** — only #1 states explicit rollback risk. #8 mentions `make check` passes. The rest leave the reviewer to infer.

Result: PRs are harder to skim, the link-to-source artifacts gets lost, and release notes (which already cite PRs) have to be re-derived every time.

## Proposed Template

Apply to every PR going forward. Drop sections that don't apply (e.g. no plan for a one-line fix).

**Title:** `[<branch-slug>] <imperative summary>` — matches the `[<slug>]` commit prefix in AGENTS.md (slug is the design doc's branch key, e.g. `[convergence-proactive-plan]`). Drop the prefix for one-liner `chore:` / `fix:` PRs.

**Body:**

```markdown
## Design
<path or "N/A">

## Plan
<path or "N/A">

## Roadmap
<path or "N/A">

## Summary
<2-4 bullets: what changed, why, blast radius>

## Changes
<bullets grouped by area or phase; cite file:line for non-obvious edits>

## Verification
<commands run + result, e.g. `make check` → clean>

## Risk
<Low/Medium/High + one-line rationale; default Low for refactors>
```

A worked example for the open #8 lives at the bottom of this ticket.

## Retroactive Application

Edit the existing PR descriptions via `gh pr edit <n> --body ...` to match the template. Squash-merge commit messages stay as-is (commit history is already fixed; this is about the PR view and the release-notes source it feeds).

| # | PR | Gap |
|---|----|-----|
| 8 | convergence-proactive-plan | Missing Design/Plan/Roadmap block; no Risk section |
| 7 | async-steps-recording-fix | Has link block ✓; body is issue-list, not Summary/Changes |
| 6 | beat-generation-split | Has link block ✓; title missing `[beat-generation-split]` is present, body OK |
| 5 | frontend-file-split | Has link block ✓; Summary is one line, no Verification |
| 4 | arc-thread-seed-refactor | Has link block ✓; Verification present, no Risk |
| 3 | compendium-scoring-cleanup | Has link block ✓; no Verification, no Risk |
| 2 | chore/improve-agents-md | Missing link block, no Verification, no Risk |
| 1 | plan/prompt-testing-and-schema-discipline | Missing link block, title uses `Design:` instead of `[design]`, Risk present but buried |

Net: 3 PRs need the link block added (#1, #2, #8); 7 PRs need Verification and/or Risk added; all 8 should get a real `## Summary` section if missing.

## Scope

- **In scope:** PR title + body template, retroactive edits to #1–#8, worked example
- **Out of scope:** Commit message conventions (already in AGENTS.md), branch naming, release-notes format, squash-merge rewrites

## Worked Example (for PR #8)

```markdown
## Design
docs/design/convergence-proactive-design.md

## Plan
plans/completed/pacing/convergence-proactive-plan.md

## Roadmap
roadmap/improvements/<this-ticket>

## Summary
- Phase machine now runs pre-ruling so the ruling prompt sees the correct phase
- Beat candidate driver format consolidated to 4 psychological types
- World step validates beat types before GMBeat schema check

## Changes
- **Phase machine (`ccya/engine/turn.py`, `ccya/engine/_pacing.py`)** — moved phase compute before ruling; added `TurnContext._convergence_score`, `_stall_floor`
- **Beat format (`ccya/prompts/extract_scene_system.j2`, `world_system.j2`)** — `bond`→`tie`, added `fear`, dropped `personality`; effect now 7-10 word psychological hint
- **World validation (`ccya/ev/checkers/convergence.py`, `ccya/ev/state_tools.py`)** — restored 6-component extraction, replaced stale `dice_weight` references
- **Config (`ccya/engine/config.py`)** — dropped `avoidance_keywords`, added 4 pacing thresholds
- **Docs** — OVERVIEW, pacing-systems, step2a, step2d, repomap, cross-module-contracts

## Verification
`make check` → clean except pre-existing lint error in `_regenerate.py`

## Risk
Low — internal refactor; phase-machine move is covered by `_phase_computed` fallback flag for any in-flight saves
```

## Done When

- [ ] Template adopted (link from AGENTS.md or a `docs/process/pr-template.md` if it warrants a file)
- [ ] PRs #1–#8 descriptions edited to match
- [ ] `gh pr list` shows consistent title format on the next 3 PRs after this one lands
