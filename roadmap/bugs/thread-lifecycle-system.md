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

### B-50.2 — Sanitizer dampening should be two-way (CRITICAL)

Sanitizer currently only downgrades urgency (17 downgrades, 0 escalations across 5 runs). **Design intent: sanitizer should be two-way — upgrade AND downgrade, match tone of scene, no bias toward either direction.** Should pull from background/dormant threads when necessary to provide escalation signals.

Current behavior: `sanitize_thread.j2:62-64` instructs "Urgency wrong?" without specifying direction. LLM only emits downgrades (urgent → normal). Creates dampening loop: downgrades → low convergence → beat_streak dominates → convergence stays at 0-3. `urgent_thread` component averages 0.40-0.60 across runs.

Design intent: Sanitizer should evaluate scene tone and thread state objectively. If a thread's urgency has genuinely escalated (new threats, imminent danger), sanitizer should upgrade it. If it has de-escalated, downgrade it. No built-in bias toward either direction. Background/dormant threads should be pulled into consideration when they have relevant urgency.

### B-50.3 — Seed threads bypass creation gates — INTENTIONAL (MEDIUM)

Seeded threads bypass cooldown (default 3 turns), cap eviction (thread_max_active=5), ID collision checks. **This is intentional design.** Seeded threads are pre-loaded premise: only a couple meant to be active, most meant to be dormant. Thread creation uses TWO paths: seeding at game start (seed.py), and explicit `thread_add` from extractor.

Evidence: noir-1930s 25t: `syndicate_retaliation` ABANDONED at T1 (seeded), `informant_network` UPDATED at T1 (seeded), `political_exposure` UPDATED at T3 (seeded), `gilded_lily_confrontation` ADDED at T15 (explicit thread_add).

Not implicit creation via thread_update — the code explicitly skips unknown IDs.

### B-50.4 — Thread one-directionality (HIGH)

Record extractor consistently emits `major_update_signal: advancement` regardless of roll band. **75-80% advancement rate is purposeful design.** Setbacks should be narratively meaningful, not mechanical. Advancement ≠ good outcome (can be bad outcomes). 3 setbacks in a row = stagnation. Thread open 20 turns = stagnation.

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

Impact: The 13-turn maximum urgency window is enforced by the sanitizer, not by decay. Decay is dead code in practice. Whether this matters depends on how the two-way sanitizer redesign handles urgency tracking.

## Fix Strategy

1. Fix `turn_state.py:443` — replace dict-iteration with model-object iteration (Condition TTL)
2. Redesign sanitizer to be two-way: upgrade AND downgrade based on scene tone, no bias, pull from background/dormant when necessary
3. Leave seed bypass as-is — intentional design for pre-loaded premise
4. Keep advancement rate at 75-80% — purposeful, setbacks should be narratively meaningful not mechanical
5. Improve compaction prompt to preserve key facts — consider programmatic quality checks
6. Accept sanitizer as enforcement mechanism for urgency decay, or investigate whether decay should fire independently

## References

- CONSOLIDATED-REPORT.md §1, §3, §4, §9, §12, §13
- validation-C-results.md (C1, C2, C3, C4, C5)
- `ccya/engine/thread_sanitizer.py`, `ccya/engine/turn_state.py`, `ccya/engine/_apply.py`, `ccya/engine/seed.py`, `ccya/prompts/sanitize_thread.j2`, `ccya/prompts/record_system.j2`
