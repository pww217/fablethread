# Findings Contents

| File | Scope |
|------|-------|
| `FINDINGS-JUNE-6.md` | All game-specific findings (Game 1: noir-1930s G1-G5; Game 2: the-fall-of-byzantium BZ1-BZ7) |
| `MOMENTUM-BEAT-FINDINGS.md` | Momentum + beat system deep-dive (MB-1–MB-7) |
| `BUGS-OBSERVATIONS.md` | Cross-game bugs, design gaps, observations (B1-B6, F1-F8, O1-O8) |
| [EVAL-FIXES.md](../EVAL-FIXES.md) | Eval system auto-checker additions needed to detect sanitizer lag (#3), thread accumulation (#5), and other eval blind spots |

**Route future findings:**

- Any game data → `FINDINGS-JUNE-6.md` (append new `## Game N` section, keep IDs sequential within each game)
- Code bugs, prompt bugs, pipeline design gaps → `BUGS-OBSERVATIONS.md`
- Deep-dives into specific systems → new `<SYSTEM>-FINDINGS.md` (like `MOMENTUM-BEAT-FINDINGS.md`)
- Eval system improvements → [EVAL-FIXES.md](../EVAL-FIXES.md)

**Cross-links:**
- Issue #3 (goal stagnation): [PRIORITIES#3](./PRIORITIES.md#3-g3j--goal-stagnation--sanitizer-too-slow-to-pivot-mh) → [FINDINGS-JUNE-6#G3](./FINDINGS-JUNE-6.md#g2---goal-stagnation--sanitizer-too-slow-to-pivot-confidence-h) → [EVAL-FIXES#issue-3](./EVAL-FIXES.md#issue-3-goal-stagnation)
- Issue #5 (thread accumulation): [PRIORITIES#5](./PRIORITIES.md#5-bz1o4--background-thread-accumulation-without-decay-mh) → [FINDINGS-JUNE-6#BZ1](./FINDINGS-JUNE-6.md#bz1-h-background-threads-accumulate-forever-without-decay) → [BUGS-OBSERVATIONS#O4](./BUGS-OBSERVATIONS.md#o4-auto-demote-arc-threads-to-latent) → [EVAL-FIXES#issue-5](./EVAL-FIXES.md#issue-5-background-thread-accumulation)
