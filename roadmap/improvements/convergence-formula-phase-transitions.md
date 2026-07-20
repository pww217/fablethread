---
title: "Convergence formula range and phase transition conflicts"
status: done
urgency: 2
size: large
created: 2026-07-19
ticket_id: I-42
completed: 2026-07-20
labels: [pacing, convergence, phases]
design:
plan:
pr:
  url:
  branch:
---

## Description

Bundle of pacing engine improvements rooted in `_pacing.py` and `narrate.py`. Five findings validated across 5 eval runs (2026-07-17_0.32.1_2e3d0188). Core issue: convergence formula compressed to 0-3 range, phase transitions conflict with extension logic, BREATHER amplifies dampening.

## Findings

### I-42.1 — Convergence limited dynamic range — WON'T DO

Convergence rarely exceeds 3-4. Typical range 0-3. Formula max is 6. Components: urgent_thread (0-2) + threat_thread (0-1) + beat_streak (0-1) + roll_starvation (0-1) + threat_density (0-1).

- `beat_streak`: avg 0.68-0.92 (always 0 or 1, threshold too easy)
- `threat_thread`: avg 0.56-1.00
- `urgent_thread`: avg 0.40-0.60 (dampening loop → two-way sanitizer redesign should fix)
- `roll_starvation`: avg 0.00-0.12 (edge case, not core convergence)
- `threat_density`: avg 0.00-0.16 (edge case, not core convergence)

Assessment: beat_streak and threat_thread are the core convergence drivers. roll_starvation and threat_density are edge case handling. Current behavior is acceptable.

### I-42.2 — BREATHER uses smoothed convergence — RESOLVED

All phase transitions now use smoothed convergence. No action needed.

### I-42.3 — BREATHER amplifies dampening — ACCEPTABLE

BREATHER resets convergence to 0-1 and threads lose urgency (sanitizer downgrades during 1-2 turn BREATHER). After breather exits, convergence must rebuild from scratch.

Cycle: BREATHER → RISING → convergence climbs to 2-3 → CLIMAX → sanitizer downgrades → convergence drops → back to RISING (never CLIMAX again).

Evidence: 5 BREATHER→RISING→CLIMAX cycles across runs. BREATHER duration: 1-2 turns. No minimum duration enforcement (breather_max_turns=3). After breather exit, convergence climbs from 0-1 back to 2-3 within 4-9 turns.

Assessment: This cycle is acceptable behavior. BREATHER is meant to be a clean break — the dampening is a feature, not a bug.

### I-42.4 — Curtain call — RESOLVED (removed in commit 1b016655)

Curtain call enters "forced" tier at `climax_turn_count >= limit-1` (T3 of CLIMAX), telling Narrator "MUST resolve" threads. Extension evaluation at `climax_turn_count >= limit` (T4), requiring `convergence >= 3 AND urgent_thread > 0`.

Self-fulfilling prophecy: Record mandates urgency in CLIMAX → Sanitizer downgrades → Convergence drops → Extension fails → CLIMAX ends quickly.

Evidence: 3 of 5 runs extended CLIMAX past limit=4. CLIMAX duration: noir 1 turn, zs(second) 1 turn, sw 10 turns, gp 7 turns, aw2 7 turns.

Decision: Remove curtain call entirely. It adds complexity with no benefit.

### I-42.5 — Rushed endings — WON'T DO

Side effect of other pacing issues. No action needed.

## Fix Strategy

1. Remove curtain call entirely — `climax_curtain_call` logic in `_pacing.py`, `narrate.py`, and `narrate_system.j2`

## References

- CONSOLIDATED-REPORT.md §5, §6, §7, §8, §15
- validation-A-results.md (A1-A4, A6)
- `ccya/engine/_pacing.py`, `ccya/engine/narrate.py`, `ccya/prompts/narrate_system.j2`
