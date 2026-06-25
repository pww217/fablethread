---
title: Condition TTL System
status: done
urgency: 3
size: medium
created: 2025-06-25
design: plans/condition-ttl-plan.md
labels:
  - conditions
  - engine
---

# Condition TTL System

Re-introduce TTL-based auto-expiration for player conditions. Conditions with `turns_remaining` decrement each turn and are auto-removed when hitting 0. `"permanent"` = permanent (never expires). Engine assigns a default TTL (10 turns) when the LLM omits it.

Duration bands: sensory (1-2), minor (3-4), significant (5-6), major (7+), permanent.

**Origin:** Eval 5-Pack 2026-06-24 (`roadmap/bugs/eval-5pack-2026-06-24.md`), Bug #2 — Duplicate Condition Adds. Without TTL, conditions persist forever because the extractor almost never removes them. The cognitive load of tracking expiration for every condition is too high. TTL is the **primary** mechanism for condition lifecycle — the engine auto-expires sensory/minor/significant conditions. The extractor only needs to reason about major (7+) and permanent conditions.

Plan: `plans/completed/engine/condition-ttl-plan.md`

**Implemented:** 2026-06-25. All 7 steps completed. Lint + typecheck pass. No deviations from plan.
