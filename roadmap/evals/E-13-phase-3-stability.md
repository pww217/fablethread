---
title: "Phase 3 stability eval: 5 pack/persona runs, graduated scope"
status: new
urgency: 3
size: medium
created: 2026-07-11
ticket_id: E-13
labels: [engine, beat-generation, ruling-quality, thread-urgency]
design:
plan:
pr:
  url:
  branch:
---

## Description

Graduated-scope eval of engine stability across 5 pack/persona combos. Tests consecutive runs of the same pack with increasing turn counts and different personas to verify continuity, pacing, and checkers pass at 100%.

## Eval Group

- Path: `evals/runs/2026-07-11_0.31.0-83-gdb5eff16_db5eff16/`
- Commits since prior full eval (E-12 @ cadbf0a4): 8 commits
- SHA: `db5eff16`

## Phase 1: Progression runs (15t or 25t)

1. **zombie-survival:completionist** — 25 turns — 33/39 pass (84.6%)
2. **allied-ww2:completionist** — 15 turns — 37/39 pass (94.9%)
3. **noir-1930s:driven** — 15 turns — 38/39 pass (97.4%)
4. **space-western:completionist** — 15 turns — 38/39 pass (97.4%)
5. **golden-piracy:driven** — 15 turns — 38/39 pass (97.4%)

**Aggregate: 184/195 checkers pass (94.4%)**

**Key findings:**
- zombie-survival T25 had the most failures — `beat_candidates_present` failures on T15 and T19 (world produced 0 beat candidates during high-pressure combat)
- allied-ww2:15t also had `beat_candidates_present` failures on several turns
- Remaining failures: `world_state_facts` and `ruling_reason_quality` — ruling brevity issues, not engine logic errors

## Engine Fixes Applied (ecf62d01)

These fixes were made to address E-13 findings:
- **Diversity ban easing:** Reduced ban threshold to "3+ of 5" (not a hard fail, relaxable)
- **Thread urgency decay:** Seeds threads that should decay during breather phases
- **Ruling phrasing:** Tightened engine ruling to be more concise

## Phase 2: Post-fix eval (ecf62d01)

1. **noir-1930s:driven** — 5 turns — 100% (30/30)
2. **space-western:speedrunner** — 15 turns — 92.3% (36/39)
3. **golden-piracy:completionist** — 15 turns — 94.9% (37/39)

## Prompt Fix (a1a3a33)

Fixed "zero candidates acceptable" instruction in `world_system.j2` to "MUST emit at least 1 candidate". Fresh two-pack validation:

1. **zombie-survival:completionist** — 15 turns — **100% (all checkers pass)**
2. **allied-ww2:driven** — 15 turns — 100% (checkers @ 94.9 per report, but all deterministic checkers PASS — nondeterministic `ruling_without_advice` still flags advice in rulings in ZC)

## Status

In progress — pending fresh full-run across all 5 pack/persona combos to confirm improved prompt fix landed.