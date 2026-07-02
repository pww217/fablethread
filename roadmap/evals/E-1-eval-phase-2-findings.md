---
title: "Phase 2 eval: thread_urgency_decay, extraction_retry_rates, convergence_recompute"
status: up-next
urgency: 2
size: medium
created: 2026-07-02
ticket_id: E-1
labels:
  - eval
  - engine
---

# E-1: Phase 2 eval findings

## Eval group

- **Path:** `evals/runs/2026-07-02_0.30.0-103-gf4e74db0_f4e74db/`
- **Runs:** noir-1930s:driven (5t + 15t), space-western:speedrunner (15t), golden-piracy:completionist (15t)
- **Phase reports:** PHASE-1.md, PHASE-2.md

## Findings

### 1. thread_urgency_decay not working (FAIL on all 3 runs)

Threads stay at `urgent` for 8+ turns without being demoted to `normal`/`background`.

**Example:** `syndicate_pressure` thread at `urgent` for 8 turns (should demote to `normal`), then at `normal` for 10 turns (should demote to `background`).

**Checker:** `thread_urgency_decay`

**Assessment:** Real bug. The sanitizer's urgency decay mechanism isn't working. Likely pre-existing (sanitizer logic unchanged in current changes).

### 2. extraction_retry_rates — state extractor missing condition_change_reason (FAIL on space-western, golden-piracy)

State extractor retry error: `EXTRACTION_COERCION_FAILED: condition_change_reason is required when condition changes are present`.

The state extractor is returning condition changes without the required `condition_change_reason` field.

**Checker:** `extraction_retry_rates`

**Assessment:** Pre-existing prompt issue — state extractor prompt doesn't instruct LLM to include `condition_change_reason`.

### 3. convergence_recompute mismatch (FAIL on all 3 runs)

Stored convergence scores don't match recomputed values on various turns.

**Checker:** `convergence_recompute`

**Assessment:** Likely pre-existing — formula may have changed since stored scores were computed. Not a regression.

## What was done

- Fixed StopAsyncIteration bug in extraction pipeline (I-23 Phase 3 regression)
- Phase 1: noir-1930s:driven 5 turns — all pass, no errors
- Phase 2: 3 games × 15 turns — engine stable, 3 consistent failures

## What's next

- Fix thread_urgency_decay (sanitizer urgency decay)
- Fix extraction_retry_rates (state extractor prompt)
- Investigate convergence_recompute (likely pre-existing, may not need fix)
- Resume Phase 3 if engine stable
