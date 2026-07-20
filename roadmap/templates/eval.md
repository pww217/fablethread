---
title: ""
status: new
urgency: 3
size: medium
created: YYYY-MM-DD
ticket_id: E-N
labels: []
design:
plan:
pr:
  url:
  branch:
---

## Description

## Context

**Prior SHA:** (extract from newest eval group in `evals/runs/` before this one)
**Changes since last eval:** (summary of commits touching `ccya/`)

### Changes Since Last Eval

(Detail engine/prompt changes with commit hashes)

### Focus Areas

(What specific mechanics/systems to examine and why)

## Plan

### Phase 1: 1 game, 5 turns — Critical bugs
- Pack: (default: noir-1930s), Persona: (default: driven)
- Target: Game-breaking bugs, obvious failures
- Report: `evals/runs/<group>/PHASE-1.md`

### Phase 2: 3 games, 15 turns — Nuanced bugs
- Pairs: noir-1930s:driven, space-western:speedrunner, golden-piracy:completionist
- Target: Intermediate degradations, pacing issues, extraction misses
- Report: `evals/runs/<group>/PHASE-2.md`

### Phase 3: 5 games, 25 turns — Balance and long-term mechanics
- All 5 persona pairs
- Target: Balance, long-term patterns, edge cases
- Report: `evals/runs/<group>/PHASE-3.md`

### Testing Items
(List any bugs with `status: testing` that this eval should validate)

## Progress

(Update continuously as work progresses. After each phase, fix, or review, write findings here.)

### Phase 1: (status) — (date)
- Pack: (pack), Persona: (persona), Turns: (N)
- Report: `evals/runs/<group>/PHASE-1.md`
- Group: `<group>`
- Status: (checker pass/fail counts + subjective assessment)

(Findings, fixes applied, validation results)

(Commit separator if fixes were applied during this eval — see "Fixes Applied" section below)

### Phase 2: (status) — (date)
...

### Phase 3: (status) — (date)
...

## Fixes Applied

(Any fixes made during this eval. Use commit separators to delineate pre-fix vs post-fix state. This section is dynamic — add entries as fixes are made.)

↑ (prior SHA or previous commit)
────────────────────────────────────
↓ (commit hash of fix)

### Fix: (what was fixed)
- File: (file changed)
- Root cause: (brief explanation)
- Validation: (how it was verified)

↑ (commit hash above)
────────────────────────────────────
↓ (next commit)

## Checkers Results

(Compile pass/fail table. Remember: checkers are bellwethers — they signal that something *might* be healthy or unhealthy. They are not verdicts. Always pair checker results with subjective examination.)

| Checker | Phase 1 | Phase 2 | Phase 3 |
|---------|---------|---------|---------|
| (name)  | (pass/fail) | (pass/fail) | (pass/fail) |

## Deep-Dive Reviews

(If ev-review was used for targeted analysis, document findings here.)

## Next

(What's left to do. If eval is complete, note status.)

## References

(Eval group paths, relevant bug/improvement tickets, architecture docs examined)
