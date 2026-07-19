---
title: "Convergence formula range and phase transition conflicts"
status: up-next
urgency: 2
size: large
created: 2026-07-19
ticket_id: I-42
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

### I-42.1 — Convergence limited dynamic range (HIGH)

Convergence rarely exceeds 3-4. Typical range 0-3. Formula designed for 0-9 range but inputs are all compressed:
- `beat_streak`: avg 0.68-0.92 (always 0 or 1, threshold too easy)
- `threat_thread`: avg 0.56-1.00
- `urgent_thread`: avg 0.40-0.60 (dampening loop)
- `roll_starvation`: avg 0.00-0.12
- `threat_density`: avg 0.00-0.16 (never 3+ active threat threads)

Convergence distribution (25t runs): noir (0.38-2.44), space-western (0.30-2.58), golden-piracy (0.28-2.44), zombie-survival (0.26-2.36), allied-ww2 (0.22-2.58). Max value: 2.58. No run exceeds 3.

### I-42.2 — Smoothed vs raw convergence mismatch (HIGH)

`_compute_scene_phase()` receives raw convergence score for phase transitions. `_compute_pacing_context()` receives `int(smoothed_convergence)` for outcome_hint hard gate. No functional bug (smoothed >= raw when increasing), but code clarity issue.

Result: outcome_hint transitions never fire in any run (max smoothed ~3.2, threshold is 5). Phase transitions happen but outcome_hint hard gate is effectively unreachable.

### I-42.3 — BREATHER amplifies dampening (HIGH)

BREATHER resets convergence to 0-1 and threads lose urgency (sanitizer downgrades during 1-2 turn BREATHER). After breather exits, convergence must rebuild from scratch.

Cycle: BREATHER → RISING → convergence climbs to 2-3 → CLIMAX → sanitizer downgrades → convergence drops → back to RISING (never CLIMAX again).

Evidence: 5 BREATHER→RISING→CLIMAX cycles across runs. BREATHER duration: 1-2 turns. No minimum duration enforcement (breather_max_turns=3). After breather exit, convergence climbs from 0-1 back to 2-3 within 4-9 turns.

### I-42.4 — Curtain call vs extension conflict (HIGH)

Curtain call enters "forced" tier at `climax_turn_count >= limit-1` (T3 of CLIMAX), telling Narrator "MUST resolve" threads. Extension evaluation at `climax_turn_count >= limit` (T4), requiring `convergence >= 3 AND urgent_thread > 0`.

Self-fulfilling prophecy: Record mandates urgency in CLIMAX → Sanitizer downgrades → Convergence drops → Extension fails → CLIMAX ends quickly.

Evidence: 3 of 5 runs extended CLIMAX past limit=4. CLIMAX duration: noir 1 turn, zs(second) 1 turn, sw 10 turns, gp 7 turns, aw2 7 turns.

### I-42.5 — Rushed endings (MEDIUM)

Dampening loop delays CLIMAX entry, 25-turn cap limits total game length. Noir spends 22 turns in RISING before reaching CLIMAX at T25 (1 turn). Zombie-survival second CLIMAX is 1 turn.

CLIMAX start turns: sw T5/T20, gp T7/T17, aw2 T12/T22, zs T14/T25, noir T25.

## Fix Strategy

1. Scale beat_streak distribution to 0-10 — requires `beat_streak_scale` parameter and formula adjustment in `_pacing.py`
2. Align smoothed/raw usage — either both use raw score, or document smoothed as intentional design
3. Give BREATHER minimum duration enforcement — `BREATHER_min=2` before any exit
4. Delay curtain_call forced tier to T4+ or modify guidance during extension-eligible CLIMAX
5. Consider dynamic turn limits based on CLIMAX entry turn, or reduce sanitizer frequency during late-game RISING

## References

- CONSOLIDATED-REPORT.md §5, §6, §7, §8, §15
- validation-A-results.md (A1-A4, A6)
- `ccya/engine/_pacing.py`, `ccya/engine/narrate.py`, `ccya/prompts/narrate_system.j2`
