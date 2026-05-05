# rules.py — dice engine

## Public APIs

- **`resolve_check(skill, difficulty, pc_stats, pc_conditions, intent_verb, intent, rng)`** → `RulesOutcome` — 2d6 + stat_mod + diff_mod + cond_mod → Band. Pure Python, deterministic with seeded rng.

## Constants

- `DIFFICULTY_MOD` — difficulty level modifiers
- `CONDITION_MODS` — condition effect modifiers
- `GM_MOVES` — GM move classifications (5 bands: crit_fail, fail, setback, partial, success, crit_success)
- `VALID_SKILLS` — allowed skill names
- `_VERB_CATEGORY` — maps intent verbs to categories (combat, social, exploration, movement, default)
- `_DIRECTIVE_TABLE` — per-(band, category) directive text for setback/partial

## Helpers

- `roll_2d6()` — roll two six-sided dice
- `compute_band(result)` — map 2d6 result to 5-band PbtA resolution
- `conditions_modifier(conditions)` — sum condition mods
- `build_directive(band, intent_verb, skill)` — verb-differentiated directive for setback/partial; verb-stamped for other bands
- `_verb_category(intent_verb)` — lookup verb category for directive table

## Type aliases

- `SkillName` — 6 valid skills
- `Difficulty` — 5 difficulty levels
- `Band` — 5 PbtA bands: crit_fail, fail, setback, partial, success, crit_success
