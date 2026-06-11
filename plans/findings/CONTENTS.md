# Findings Contents

| File | Scope |
|------|-------|
| `FINDINGS-JUNE-6.md` | All game-specific findings (Game 1: noir-1930s G1-G5; Game 2: the-fall-of-byzantium BZ1-BZ7) |
| `MOMENTUM-BEAT-FINDINGS.md` | Momentum + beat system deep-dive (MB-1–MB-7) |
| `BUGS-OBSERVATIONS.md` | Cross-game confirmed bugs and observations needing fixes (B1–B7, O1–O8) + Completed/Superseded section |
| [FEATURE-IDEAS.md](./FEATURE-IDEAS.md) | Net-new features, improvements/bugs to implement, design questions — organized by subsystem (Game Setup, Compendium, Scene Mechanics, Narrative Setup, NPC Mechanics, Storytelling Pipeline, UI, Pipeline Efficiency, Low Priority) |
| [EVAL-FIXES.md](../EVAL-FIXES.md) | Eval system auto-checker additions needed to detect sanitizer lag (#3), thread accumulation (#5), and other eval blind spots |
| [PRIORITIES.md](./PRIORITIES.md) | Ranked priorities — critical fixes ordered by impact (13 items, most original priorities FIXED) |
| [EVAL-FINDINGS-2026-06-09.md](./EVAL-FINDINGS-2026-06-09.md) | Eval system bugs and findings from 2026-06-09 baseline run |
| [EVAL-EV-BUGS.md](./EVAL-EV-BUGS.md) | EV tooling and eval system bugs (EV-1 through EV-10, B11-B13) |

**Route future findings:**

- Any game data → `FINDINGS-JUNE-6.md` (append new `## Game N` section, keep IDs sequential within each game)
- Confirmed bugs + observations needing fixes → BUGS-OBSERVATIONS.md (superseded items go to Completed/Superseded section)
- Net-new features, improvements to implement, design questions → [FEATURE-IDEAS.md](./FEATURE-IDEAS.md) by subsystem category
- Deep-dives into specific systems → new `<SYSTEM>-FINDINGS.md` (like `MOMENTUM-BEAT-FINDINGS.md`)
- Eval system improvements → [EVAL-FIXES.md](../EVAL-FIXES.md)
- Priority assessments → [PRIORITIES.md](./PRIORITIES.md)
- Completed plans affecting findings → `plans/completed/` (e.g., `grounded-state-extraction.md` fixed B5, F-N04, F-N06, F-N07)

**Cross-links:**
- Goal stagnation (FIXED): [PRIORITIES#Previously Fixed](./PRIORITIES.md#previously-fixed-for-reference) → [FINDINGS-JUNE-6#G3](./FINDINGS-JUNE-6.md#g2---goal-stagnation--sanitizer-too-slow-to-pivot-confidence-h)
- Thread accumulation (FIXED): [PRIORITIES#Previously Fixed](./PRIORITIES.md#previously-fixed-for-reference) → [BUGS-OBSERVATIONS#O4](./BUGS-OBSERVATIONS.md#o4-auto-demote-arc-threads-to-latent)
- Seed/hints conflict (NEW): [PRIORITIES#1](./PRIORITIES.md#1-f-n08f-n09--seed-json-vs-hints-conflict-hh) → [FEATURE-IDEAS#F-N08](./FEATURE-IDEAS.md#f-n08-seed-json-vs-hints-conflict-net-new)
