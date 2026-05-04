# rules.py — dice engine

## Public APIs

- **`resolve_check(skill, difficulty, pc_stats, pc_conditions, intent_verb, intent, rng)`** → `RulesOutcome` — 2d6 + stat_mod + diff_mod + cond_mod → Band. Pure Python, deterministic with seeded rng.

## Constants

- `DIFFICULTY_MOD` — difficulty level modifiers
- `CONDITION_MODS` — condition effect modifiers
- `GM_MOVES` — GM move classifications
- `VALID_SKILLS` — allowed skill names

## Helpers

- `roll_2d6()` — roll two six-sided dice
- `compute_band(result)` — map 2d6 result to PbtA band
- `conditions_modifier(conditions)` — sum condition mods
- `build_directive(band)` — build GM directive from band

## Type aliases

- `SkillName` — 6 valid skills
- `Difficulty` — 5 difficulty levels
- `Band` — 7 PbtA bands (disaster, failure, mixed, weak hit, strong hit, etc.)
