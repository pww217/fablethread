# rules.py — dice engine

## Public APIs

- **`resolve_check(*, skill, difficulty, pc_stats, pc_conditions, intent_verb, intent, rng)`** → `RulesOutcome` — 2d6 + stat_mod + diff_mod + cond_mod → Band. Pure Python, deterministic with seeded rng.

## Constants

- `DIFFICULTY_MOD` — difficulty level modifiers
- `CONDITION_MODS` — condition effect modifiers
- `GM_MOVES` — GM move classifications (6 bands: crit_fail, fail, setback, partial, success, crit_success)
- `MOMENTUM_DELTA` — deterministic momentum delta per band (crit_success:+2, success:+1, partial:0, setback:-1, fail:-1, crit_fail:-2)
- `VALID_SKILLS` — allowed skill names
- `_VERB_CATEGORY` — maps intent verbs to categories (combat, social, exploration, movement, default)
- `_DIRECTIVE_TABLE` — per-(band, category) directive text for setback/partial

## Helpers

- `roll_2d6(rng)` — roll two six-sided dice, returns `(die1, die2)`
- `compute_band(final_total, dice)` — map 2d6 result to 6-band PbtA resolution (crit_fail on natural 2, crit_success on natural 12)
- `conditions_modifier(skill, conditions)` — sum condition mods for a given skill
- `build_directive(band, intent_verb, skill)` — verb-differentiated directive for setback/partial; verb-stamped for other bands
- `_verb_category(intent_verb)` — lookup verb category for directive table

## Type aliases

- `SkillName` — 6 valid skills
- `Difficulty` — 5 difficulty levels
- `Band` — 6 PbtA bands: crit_fail, fail, setback, partial, success, crit_success
