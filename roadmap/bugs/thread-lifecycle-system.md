---
title: "Thread lifecycle system: TTL bug, dampening loop, seed bypass, compaction, decay"
status: validated
urgency: 1
size: large
created: 2026-07-19
ticket_id: B-50
labels: [threads, sanitizer, state]
design:
plan:
pr:
  url:
  branch:
---

## Description

Bundle of thread lifecycle bugs rooted in `thread_sanitizer.py`, `turn_state.py`, `_apply.py`, `seed.py`, `sanitize_thread.j2`. Six findings validated across 5 eval runs (2026-07-17_0.32.1_2e3d0188).

## Findings

### B-50.1 — Condition TTL never decrements (P0)

`turn_state.py:443` has `if not isinstance(c, dict): continue`. `state.pc.conditions` contains `Condition` model objects, so ALL conditions are skipped. TTL decrement logic is dead code.

Evidence:
- allied-ww2: `concerned` persists 24 turns (T2-T25), `exhausted` 21 turns, `rattled` 20 turns, `concussed` 19 turns
- zombie-survival: `exhausted` persists 13 turns (T13-T25), `rattled` 12 turns
- noir-1930s: `focused` 13 turns, `rattled` 12 turns
- golden-piracy: 7 concurrent conditions at T16 (limit is 5)

Impact: Conditions persist indefinitely, affecting ruling accuracy, narration accuracy, and game balance.

### B-50.2 — Sanitizer only downgrades urgency (CRITICAL)

Zero urgency escalations across all 5 runs. Every sanitizer urgency change is a downgrade (urgent → normal). `sanitize_thread.j2:62-64` instructs "Urgency wrong?" without specifying direction. No escalation guidance exists.

Impact: `urgent_thread` component (0-2 points, highest-value in convergence formula) averages 0.40-0.60 across runs (10-15/25 turns at 1). Creates feedback loop: downgrades → low convergence → beat_streak dominates → convergence stays at 0-3. Total: 0 escalations, 17 downgrades.

### B-50.3 — Seed threads bypass creation gates (CRITICAL)

Seeded threads bypass cooldown (default 3 turns), cap eviction (thread_max_active=5), ID collision checks. Not implicit creation via thread_update — the code explicitly skips unknown IDs. Thread creation uses TWO paths: seeding at game start (seed.py), and explicit `thread_add` from extractor.

Evidence: noir-1930s 25t: `syndicate_retaliation` ABANDONED at T1 (seeded), `informant_network` UPDATED at T1 (seeded), `political_exposure` UPDATED at T3 (seeded), `gilded_lily_confrontation` ADDED at T15 (explicit thread_add).

### B-50.4 — Thread one-directionality (HIGH)

Record extractor consistently emits `major_update_signal: advancement` regardless of roll band. `record_system.j2:12` allows `advancement|setback` but LLM consistently emits `advancement`.

Signal distribution (140 turns across 9 runs): 148 advancement vs 18 setback (10.8% setback rate). noir-1930s: 4.3-20% setback. golden-piracy: 0% setback in both runs.

Impact: Thread urgency/progress state drifts upward. Threads appear to be progressing even when the player is failing.

### B-50.5 — Sanitizer compaction loses factual content (MEDIUM)

Compaction is LLM-driven via `sanitize_thread.j2`, not a programmatic algorithm. Significant factual loss.

Examples from noir-1930s 25t:
- T5: `political_exposure` 3 → 1 entries (lost "Syndicate connections confirmed", "Arthur Sterling identified")
- T15: `political_exposure` 9 → 4 entries (lost Sterling/warehouse/Vane/witness/cigarette case/newsboy)
- T20: `gilded_lily_confrontation` 4 → 1 entries (lost "Guards actively pursuing", "Gregory Ford successfully evaded")

### B-50.6 — Urgency decay never fires (MEDIUM)

Zero `urgency_decay` logs across all 11 runs (140+ turns). The decay mechanism exists in `turn_state.py:176-219` but is effectively dead code.

Root cause: Extractor resets `urgency_set_turn` every turn it updates a thread (turn_state.py:66). Sanitizer also resets it (thread_sanitizer.py:414). Auto-dormant resets it too (turn_state.py:166, 184). Decay is always preempted.

## Fix Strategy

1. Fix `turn_state.py:443` — replace dict-iteration with model-object iteration (Condition TTL)
2. Add urgency escalation guidance to `sanitize_thread.j2` — if Record set urgency urgent within last 2 turns, preserve it
3. Add thread_add-style validation (cooldown, cap eviction) to seeded threads in `seed.py`
4. Strengthen `record_system.j2` — make setback on fail rolls a binding instruction
5. Add programmatic compaction quality checks — count of advancement vs setback entries preserved
6. Fix urgency decay — either make it fire even when extractor/sanitizer touch the thread, or accept sanitizer as the enforcement mechanism

## References

- CONSOLIDATED-REPORT.md §1, §3, §4, §9, §12, §13
- validation-C-results.md (C1, C2, C3, C4, C5)
- `ccya/engine/thread_sanitizer.py`, `ccya/engine/turn_state.py`, `ccya/engine/_apply.py`, `ccya/engine/seed.py`, `ccya/prompts/sanitize_thread.j2`, `ccya/prompts/record_system.j2`
