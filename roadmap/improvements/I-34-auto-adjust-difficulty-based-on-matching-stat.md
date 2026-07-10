---
title: "Auto-adjust difficulty based on matching stat"
status: idea
urgency: 2
size: small
created: 2026-07-09
ticket_id: I-34
labels:
  - engine
  - rules
  - gameplay
---

## Problem

The ruling LLM defaults to "hard" for almost all tense situations — combat, social confrontation, anything with stakes. Even when the PC's matching stat is 4, they get no advantage on difficulty assessment. This creates frustrating loops where high-stats feel no different from mid-stats on rolls.

## Proposal

Add auto-adjustment of difficulty in `resolve_check()` based on matching stat value. The LLM still *assigns* the difficulty, but the engine applies a bonus/penalty before the roll.

### Difficulty tiers

```
trivial (+2) → easy (+1) → normal (0) → hard (-1) → extreme (-2)
```

### Stat-based adjustment

| Stat | Effect |
|------|--------|
| 4 | Downgrade one tier (easier) |
| 3 | No adjustment (baseline) |
| 2 | No adjustment (baseline) |
| 1 | Upgrade one tier (harder) |

Examples:
- Charisma 4 vs "hard" → becomes "normal" (-1 → 0)
- Strength 1 vs "normal" → becomes "hard" (0 → -1)
- Wits 4 vs "easy" → becomes "trivial" (+1 → +2)
- Dexterity 3 vs "hard" → stays "hard" (-1)

## Implementation

Single function in `ccya/rules.py`, called from `resolve_check()` before computing `diff_mod`:

```python
_DIFFICULTY_ORDER = ["trivial", "easy", "normal", "hard", "extreme"]

def _adjust_difficulty(difficulty: str, stat_value: int) -> str:
    idx = _DIFFICULTY_ORDER.index(difficulty)
    if stat_value == 4:
        idx = max(0, idx - 1)  # downgrade one tier
    elif stat_value == 1:
        idx = min(4, idx + 1)  # upgrade one tier
    return _DIFFICULTY_ORDER[idx]
```

Called in `resolve_check()` at line 164:

```python
difficulty = _adjust_difficulty(difficulty, stat_value)
diff_mod = mods[difficulty]
```

## What stays the same

- LLM still assigns difficulty — this is a post-hoc adjustment, not a replacement
- `outcome.difficulty` in `RulesOutcome` shows the *adjusted* difficulty (the one actually used for the roll)
- No prompt changes needed — this is pure engine logic

## What to consider

- Should `outcome.difficulty` show the original or adjusted difficulty? Showing adjusted is clearer for the player ("you rolled normal" makes more sense than "you rolled hard" when the roll used normal).
- Skill 3 gets no bonus — is this too binary? Could add a +1 modifier on top for stat 3, but the user seemed to prefer the tier-based approach.
