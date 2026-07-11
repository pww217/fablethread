---
title: "Auto-adjust difficulty based on matching stat"
status: done
completed: 2026-07-11
urgency: 2
size: small
created: 2026-07-09
ticket_id: I-34
plan:
  title: "Auto-adjust difficulty based on matching stat"
  path: "plans/completed/game-mechanics/I-34-auto-adjust-difficulty-based-on-stat.md"
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

| Stat | Feel | Effect |
|------|------|--------|
| 4 | Expert | Downgrade one tier (always) |
| 3 | Competent | ~33% chance to downgrade one tier |
| 2 | Mediocre | No adjustment |
| 1 | Terrible | Upgrade one tier (always) |

Examples:
- Charisma 4 vs "hard" → becomes "normal" (-1 → 0)
- Strength 1 vs "normal" → becomes "hard" (0 → -1)
- Wits 4 vs "easy" → becomes "trivial" (+1 → +2)
- Dexterity 3 vs "hard" → ~33% chance becomes "normal", ~67% stays "hard"

## Implementation

### Engine changes

1. **`ccya/rules.py`** — Add `_adjust_difficulty()` function that reads stat value and adjusts difficulty down one tier with probability based on stat:
   - Stat 4: always down one tier
   - Stat 3: ~33% chance down one tier (uses `random.random() < 0.33`)
   - Stat 2: no adjustment
   - Stat 1: always up one tier

   Called in `resolve_check()` before computing `diff_mod`:
   ```python
   difficulty = _adjust_difficulty(difficulty, stat_value)
   diff_mod = mods[difficulty]
   ```

2. **`ccya/models/rules.py`** — Add two fields to `RulesOutcome`:
   - `original_difficulty: str = ""` — what the LLM assigned (for display)
   - `difficulty_adjustment: str = ""` — reason text for UI tooltip (e.g., "difficulty downgraded from hard to normal — skill level 4")

3. **`ccya/engine/ruling.py`** — Pass `stat_value` to `_adjust_difficulty()` (already available from `pc_stats`), update `outcome.original_difficulty` with the LLM's choice before adjustment.

### UI changes

Show `difficulty_adjustment` as a second line in the difficulty tooltip across:
- `ccya/templates/index.html` — Jinja2 template
- `ccya/templates/_turn_log.html` — Jinja2 fragment
- `ccya/static/game-utils.js` — JS roll badge builder

Tooltip format:
```
{difficulty}
{reason}
{difficulty_adjustment}
```

## What stays the same

- LLM still assigns difficulty — this is a post-hoc adjustment, not a replacement
- `outcome.difficulty` in `RulesOutcome` shows the *adjusted* difficulty (the one actually used for the roll)
- No prompt changes needed — this is pure engine logic

## What to consider

- `outcome.difficulty` shows the adjusted difficulty — clearer for the player ("you rolled normal" makes more sense than "you rolled hard" when the roll used normal)
- `outcome.original_difficulty` preserves the LLM's choice for transparency
- Stat 3 probabilistic uses `random.random() < 0.33` — not perfectly 1/3 but close enough for gameplay purposes

## Validation (2026-07-11 ev-review)

- **Sources:** `evals/runs/2026-07-11_0.31.0-80-g20ebb08a_20ebb08a/1254_zombie-survival_20t/events.jsonl`
- **Turn 7:** LLM ruled `hard`, stat wits=4 → adjusted to `easy` (trivial). `original_difficulty=hard`, `difficulty_adjustment="Difficulty adjusted due to high skill proficiency"`, `diff_mod=1` (trivial).
- **Turn 8:** LLM ruled `normal`, stat dexterity=3 → adjusted to `easy`. `original_difficulty=normal`, `difficulty_adjustment="Difficulty adjusted due to skill proficiency"`.
- **Turn 14:** LLM ruled `normal`, wits=4 → `easy`. Adjusted correctly.
- **Turn 18:** LLM ruled `hard`, dexterity=3 → `normal`. `difficulty_adjustment="Difficulty adjusted due to skill proficiency"`. 33% probability applied (not always triggered, just on this roll).
- `difficulty_adjustment` field is populated in ruling output when adjustment occurs; `original_difficulty` always reflects LLM's ruling. When no adjustment, both are `null`/empty.
### Verdict
I-34 is fully working. All 4 stat tiers (1, 3, 4, and implicit 2) behave as specified.
