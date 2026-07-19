---
title: "Low-priority: location checker, untested paths, resolved items"
status: canceled
urgency: 4
size: small
created: 2026-07-19
ticket_id: I-44
labels: [low-priority, deferred]
design:
plan:
pr:
  url:
  branch:
---

## Description

Low-priority items from validated findings that are either trivial fixes, untested code paths, or already resolved. Defer until higher-priority tickets are complete.

## Findings

### I-44.1 — Location description checker — DIRECT BUG (MEDIUM)

`ccya/ev/checkers/state.py:47` uses AND logic: fail only if `words < 15 AND sentences < 1`. All descriptions have at least 1 sentence, so they pass even though they're clearly too short (12-19 words typical, all under 30).

This is a direct bug. Fix: Switch from AND logic to OR logic (fail if words < min OR sentences < min), or raise minimum sentence threshold to 2.

### I-44.2 — Untested mechanics: update+resolve conflict (LOW)

Detection code exists at `turn_state.py:586-593`: `{u.id for u in thread_update} & {r.id for r in thread_resolve}`. Zero conflicts found across 140 turns. LLM never emits both an update and resolve for the same thread in the same turn.

Not a bug — just untested code path. Create targeted eval scenario to exercise.

### I-44.3 — Untested mechanics: cap, cooldown, culling, dedup (LOW)

7 of 15 thread mechanics not exercised in these runs:
- Cap eviction (thread_max_active=5): never exceeded
- Cooldown (3 turns): seed threads bypass, record threads spaced sufficiently
- Culling (≥3 dormant): threads resolved before threshold reached
- Dedup (70% overlap): LLM produced sufficiently distinct progress entries
- Arc resolution: no arc_resolve emitted in any run
- Goal updates: no goal_update emitted in any run
- Arc resolve lifecycle: no resolved_arcs in any run

Create targeted eval scenarios to exercise these mechanics.

### I-44.4 — World state TTL expiry never tested (LOW)

golden-piracy has facts with `expires_turn=28` and `expires_turn=30`. Runs only go to T25, so expiry mechanism never exercised. Untested ground — may work or may have bugs.

Run a 30+ turn eval to exercise expiry mechanism.

### I-44.5 — Auto-dormant mystery resolved (no action needed)

`gilded_lily_confrontation` dormant state transitions fully traceable through sanitizer events. dormant=True set at T25 by sanitizer, not at T20 as previously claimed. No mystery — state transition is traceable. Zero auto-dormant logs across all runs suggests auto-dormant may not be firing when expected, but this is low priority.

## References

- CONSOLIDATED-REPORT.md §16, §18, §19, §20, §21
- validation-C-results.md (C5)
- validation-D-results.md
