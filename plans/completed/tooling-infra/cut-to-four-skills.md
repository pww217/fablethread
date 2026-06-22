# Cut Skill System to Four Core Skills

## Status
`completed`

Committed: 149b3a7

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Remove lore and resolve | Delete both skills from all code, prompts, UI, and docs |

## Objective
The current 6-skill system includes `lore` and `resolve` which never appear in practice — eval runs consistently flag them as missing across full play sessions. Both skills lack a distinct active-verb domain: lore overlaps wits (cognition), and resolve overlaps the existing physical/social skills (endurance already covered by strength/dexterity, social resistance by charisma). Cutting to the four genuinely distinct skills (strength, dexterity, wits, charisma) eliminates dead stat weight and stops the eval coverage gap flag from firing on a structural limitation rather than a real problem.

## Non-goals
- Does not rename or redefine any remaining skill.
- Does not change the dice resolution logic in `rules.py` beyond the skill set constant and CONDITION_MODS cleanup.
- Does not migrate existing save files — no backward compatibility required per AGENTS.md. Running saves with lore/resolve stats will load without error but `_validate_stats` is only called at new-game time, so they remain playable.
- Changes stat point budget from 12–16 (6 skills) to 8–12 (4 skills). Per-skill range stays 1–4.
- Updates eval scenarios, rubrics, and documentation to reflect the reduced skill set.

---

## Implementation — Phase 01: Remove lore and resolve

### Files to pull for context
- `ccya/models.py`
- `ccya/rules.py`
- `ccya/server/app.py`
- `ccya/prompts/ruling_system.j2`
- `ccya/prompts/generate_seed_system.j2`
- `ccya/templates/index.html`
- `ccya/templates/_state_right.html`
- `evals/rubrics/narrative_interplay.md`
- `ccya/eval/engine_mirror.py`
- `evals/scenarios/eval_coverage_gap.py`
- `evals/packs/eval-pack/seed_state.yaml`
- `tests/conftest.py`
- `docs/repomap.md`
- `ccya/state/io.py`
- `ccya/prompts/context.py`
- `ccya/prompts/extract_state_system.j2`

---

### Detailed steps

#### Step 1.1 — Update SkillName type alias

**File:** `ccya/models.py`

**What:** Remove `"lore"` and `"resolve"` from the `SkillName` Literal.

**Why:** `SkillName` is the canonical type constraint used across the pipeline. All downstream validation derives from it.

**Code Snippet**
```python
SkillName = Literal["strength", "dexterity", "wits", "charisma"]
```

**Validation:** `grep -n "SkillName" ccya/models.py` confirms only 4 values. `make check` will catch any type mismatches downstream.

---

#### Step 1.2 — Update VALID_SKILLS constant

**File:** `ccya/rules.py`

**What:** Remove `"lore"` and `"resolve"` from the `VALID_SKILLS` frozenset.

**Why:** `VALID_SKILLS` is used at runtime for skill validation in the dice resolver. Must match `SkillName`.

**Code Snippet**
```python
VALID_SKILLS: frozenset[str] = frozenset(
    ["strength", "dexterity", "wits", "charisma"]
)
```

**Validation:** `grep -n "VALID_SKILLS" ccya/rules.py` confirms 4 values.

---

#### Step 1.2b — Remove resolve from CONDITION_MODS

**File:** `ccya/rules.py`

**What:** Remove `"resolve"` entries from all condition modifiers in the `CONDITION_MODS` dict:
- `"exhausted": {"strength": -1, "dexterity": -1}` (remove `"resolve": -1`)
- `"drugged": {"wits": -1}` (remove `"resolve": -1`)
- `"frightened": {"charisma": -1}` (remove `"resolve": -1`)
- `"shaken": {}` — remove the entire entry since resolve was its only modifier

**Why:** `CONDITION_MODS` maps condition IDs to skill modifiers. The engine applies these via `conditions_modifier(skill, pc_conditions)` in `resolve_check()`. After removing resolve from VALID_SKILLS, no PC can have a resolve stat, so these modifiers become dead code that silently apply against non-existent values. Clean removal prevents confusion and keeps the conditions system accurate for remaining skills.

**Validation:** `grep -n "resolve" ccya/rules.py` confirms only matches are in comments or unrelated words (not skill references).

---

#### Step 1.3 — Update stat validation in server

**File:** `ccya/server/app.py`

**What:** Remove `"lore"` and `"resolve"` from the `SKILLS` set in `_validate_stats`.

**Why:** `_validate_stats` enforces that a submitted character has exactly the valid skill keys. With 6 skills, new-game requests with only 4 stats would be rejected.

**Code Snippet**
```python
def _validate_stats(stats: dict[str, int]) -> bool:
    SKILLS = {"strength", "dexterity", "wits", "charisma"}
    if set(stats.keys()) != SKILLS:
        return False
    if not all(isinstance(v, int) and 1 <= v <= 4 for v in stats.values()):
        return False
    total = sum(stats.values())
    return 8 <= total <= 12


def main() -> None:
```

**Validation:** Submit a new-game request via curl with only 4 stats; confirm 200. Submit with lore/resolve; confirm 422. Total must be between 8 and 12 inclusive (was 12–16 for 6 skills).

---

#### Step 1.3b — Update default state in migration function

**File:** `ccya/state/io.py`

**What:** Remove `"lore": 2,` and `"resolve": 2,` from the stats dict inside `_default_state()` (lines 60–67). The resulting stats should be:
```python
"stats": {
    "strength": 2,
    "dexterity": 2,
    "wits": 2,
    "charisma": 2,
},
```

**Why:** `_default_state()` is returned when no save file exists or YAML parsing fails. It must match the new 4-skill schema. The migration function `_migrate_v0_to_v1` itself (which handles a legacy YAML tag corruption fix) does not reference lore/resolve skills and should be left intact — only the default state values change.

**Validation:** `grep -n "lore\|resolve" ccya/state/io.py` confirms no skill references remain in `_default_state()`. The migration function itself (`_migrate_v0_to_v1`) is preserved as-is since it handles YAML tag corruption, not skill migration.

---

#### Step 1.4 — Update ruling system prompt

**File:** `ccya/prompts/ruling_system.j2`

**What:** Remove `lore` and `resolve` from the `skill` field enum in the check object schema.

**Why:** The ruling LLM reads this schema to know which skills are valid when deciding whether a check is required and which skill applies. Leaving stale values risks the model selecting them.

**Code Snippet**

Find the line:
```
  - `skill`: strength|dexterity|wits|lore|charisma|resolve.
```
Replace with:
```
  - `skill`: strength|dexterity|wits|charisma.
```

**Validation:** Read the rendered prompt via `curl localhost:8000` or inspect template directly; confirm lore/resolve absent.

---

#### Step 1.5 — Update seed generation system prompt

**File:** `ccya/prompts/generate_seed_system.j2`

**What:** Remove `lore` and `resolve` from the `stats` schema in the PC TypeScript-style definition block.

**Why:** The seed LLM uses this schema to generate initial PC stats. It must not emit lore/resolve keys.

**Code Snippet**

Find the stats block (approximate):
```
stats: {strength: int, dexterity: int, wits: int, lore: int, charisma: int, resolve: int}
```
Replace with:
```
stats: {strength: int, dexterity: int, wits: int, charisma: int}
```

Also update the `pc.stats` field guidance text on line 118 from "six integer values, range 1–4, total 12–18" to "four integer values, range 1–4, total 8–12".

**Validation:** Generate a new seed and confirm the resulting `state.yaml` has exactly 4 stat keys.

---

#### Step 1.5b — Update extract state condition guidance

**File:** `ccya/prompts/extract_state_system.j2`

**What:** Remove resolve skill references from condition generation guidance:
- Line 103: Remove `- Failed \`resolve\` → consider \`shaken\`` entirely (shaken was only triggered by failed resolve; remove the rule)
- Line 105: Change `Failed \`strength\`/\`dexterity\`/\`resolve\` with sustained effort → consider \`exhausted\`` to `Failed \`strength\`/\`dexterity\` with sustained effort → consider \`exhausted\``

**Why:** The extract state LLM uses this guidance to decide which conditions to add based on roll outcomes. References to resolve as a skill will cause the model to suggest shaken/exhausted for non-existent resolve rolls, creating orphan conditions that have no matching stat to apply CONDITION_MODS against.

**Validation:** Read file; confirm only strength and dexterity appear in condition guidance lines 102–105. No lore or resolve skill references remain.

---

#### Step 1.6 — Update character creation UI

**File:** `ccya/templates/index.html`

**What:** Remove the `lore` and `resolve` entries from the `skills` array in the Vue/Alpine data block, update validation bounds to match new total range (8–12), update archetype descriptions, and rewrite archetype presets.

Remove these two objects from the skills array:
```js
{ key: 'lore', label: 'Lore', description: 'Knowledge, investigation, and recalling information.', value: 2 },
{ key: 'resolve', label: 'Resolve', description: 'Mental fortitude, resisting fear, and pushing through pain.', value: 2 },
```

The remaining array should be:
```js
{ key: 'strength', label: 'Strength', description: 'Force, melee combat, and soak against physical trauma.', value: 2 },
{ key: 'dexterity', label: 'Dexterity', description: 'Reflexes, ranged attacks, and avoiding danger.', value: 2 },
{ key: 'wits', label: 'Wits', description: 'Awareness, perception, and quick thinking under pressure.', value: 2 },
{ key: 'charisma', label: 'Charisma', description: 'Persuasion, leadership, and reading people.', value: 2 },
```

Update the `isValid` getter from `this.total >= 12 && this.total <= 16` to `this.total >= 8 && this.total <= 12`.

Update the `increment(statKey)` method cap from `this.total < 16` to `this.total < 12`.

Replace archetype descriptions:
```js
getArchetypeDescriptions() {
    return {
        warrior: 'A frontline fighter. High Strength and Dexterity for melee combat and endurance.',
        scout: 'A nimble tracker. High Dexterity and Wits for stealth, perception, and reflexes.',
        scholar: 'A learned researcher. High Wits and Charisma for knowledge, investigation, and influence.',
        charmer: 'A charismatic leader. High Charisma and Wits for persuasion, leadership, and influence.',
        survivor: 'A resilient survivor. High Strength and Dexterity for endurance, toughness, and adaptability.',
    };
},
```

Replace archetype presets (4 skills only, totals adjusted to stay within 8–12):
```js
const archetypes = {
    warrior:   { strength: 3, dexterity: 3, wits: 2, charisma: 2 },      // total 10
    scout:     { strength: 2, dexterity: 4, wits: 3, charisma: 2 },       // total 11
    scholar:   { strength: 2, dexterity: 2, wits: 4, charisma: 3 },      // total 11
    charmer:   { strength: 2, dexterity: 2, wits: 2, charisma: 4 },      // total 10
    survivor:  { strength: 3, dexterity: 3, wits: 2, charisma: 2 },       // total 10
};
```

**Validation:** Load character creation page; confirm only 4 stat sliders appear. Confirm validation requires total between 8 and 12 inclusive. Archetype presets should all produce valid totals within range.

---

#### Step 1.6b — Update right sidebar skill descriptions

**File:** `ccya/templates/_state_right.html`

**What:** Remove lore and resolve from the `_stat_tips` dict (lines 17–24):
```jinja2
{% set _stat_tips = {
    "strength": "Physical force, melee, lifting, breaking, soak, endure pain",
    "dexterity": "Agility, stealth, ranged attacks, fine motor, dodge, pickpocket",
    "wits": "Quick thinking, perception, deduction, hacking under pressure, spot a lie",
    "charisma": "Persuade, deceive, charm, negotiate, perform, seduce, intimidate by presence"
} %}
```

**Why:** The right sidebar displays skill tooltips to players during gameplay. Lore and resolve will appear as dead skills in production if not removed from this template.

**Validation:** Load a running game; confirm only 4 stat tooltips appear in the player card of the right sidebar.

---

#### Step 1.7 — Update eval engine mirror

**File:** `ccya/eval/engine_mirror.py`

**What:** Remove `"lore"` and `"resolve"` from the `SKILLS` constant.

**Why:** `SKILLS` in the engine mirror is used by eval scenarios to programmatically reference valid skills. Stale values will cause scenarios that iterate over skills to exercise dead checks.

**Code Snippet**
```python
SKILLS: frozenset[str] = frozenset(["strength", "dexterity", "wits", "charisma"])
```

**Validation:** Confirm `engine_mirror.SKILLS` has 4 values.

---

#### Step 1.8 — Update eval skill coverage rubric

**File:** `evals/rubrics/narrative_interplay.md`

**What:** Remove `lore` and `resolve` from the skill coverage check description.

**Why:** The judge rubric flags missing skills by name. Leaving old names means the judge will always flag lore/resolve as missing — the exact false positive we're eliminating.

**Code Snippet**

Find:
```
- **Skill coverage**: list which of the 6 skills (`strength, dexterity, wits, lore, charisma, resolve`) appeared in dice rolls. Flag if a skill never appeared across the entire run.
```
Replace with:
```
- **Skill coverage**: list which of the 4 skills (`strength, dexterity, wits, charisma`) appeared in dice rolls. Flag if a skill never appeared across the entire run.
```

**Validation:** Read file; confirm 4 skills listed.

---

#### Step 1.9 — Update eval coverage gap scenario

**File:** `evals/scenarios/eval_coverage_gap.py`

**What:** Remove lore/resolve from any turn assertions or skill variety checks that enumerate all 6 skills.

**Why:** The scenario is designed to exercise all valid skills. If it still tries to assert lore or resolve coverage, it will always fail.

**Code Snippet**

Read the file first. Find any assertion or comment referencing all 6 skills and reduce to 4. Example pattern to update:
```python
# Before
EXPECTED_SKILLS = {"strength", "dexterity", "wits", "lore", "charisma", "resolve"}

# After
EXPECTED_SKILLS = {"strength", "dexterity", "wits", "charisma"}
```

Apply the same change to any inline set literals or comments enumerating the skill list.

**Validation:** Read file; confirm no references to lore or resolve remain.

---

#### Step 1.9b — Update eval coverage gap scenario T8 expectation

**File:** `evals/scenarios/eval_coverage_gap.py`

**What:** Change line 119 from `"rules.required=true skill=lore (tactical analysis)"` to `"rules.required=true skill=wits (tactical analysis, perception under pressure)"`.

**Why:** The scenario's T8 turn ("I study the old battle maps in the village hall") was designed to exercise lore. Since lore is removed, wits is the closest remaining skill for tactical analysis and perception-based reasoning. This ensures the eval continues exercising a distinct 5th skill beyond strength/dexterity/charisma used in earlier turns.

**Validation:** Read file; confirm T8 expects `skill=wits` instead of `skill=lore`. No other lore references remain in any scenario file.

---

#### Step 1.9c — Update prompt context comment

**File:** `ccya/prompts/context.py`

**What:** Change line 33 from:
```python
stats: dict[str, int]  # {strength/dexterity/wits/lore/charisma/resolve: int}
```
to:
```python
stats: dict[str, int]  # {strength/dexterity/wits/charisma: int}
```

**Why:** Stale comments mislead future developers on the expected shape of player stats. The comment is a docstring hint, not enforced code, but should be accurate.

**Validation:** `grep -n "lore\|resolve" ccya/prompts/context.py` confirms no skill references remain (only unrelated words like "resolve" in non-skill contexts).

---

#### Step 1.10 — Update eval pack seed state

**File:** `evals/packs/eval-pack/seed_state.yaml`

**What:** Remove `lore: 2` and `resolve: 3` from `pc.stats`. The resulting stats should be:
```yaml
stats:
  strength: 3
  dexterity: 3
  wits: 2
  charisma: 3
```

The new total is 11, which falls within the valid range of 8–12. No redistribution needed — all values remain in the 1–4 per-skill range and the total constraint (8 ≤ total ≤ 12) is satisfied.

**Why:** The eval pack seed is loaded directly into the engine at eval time. If it contains invalid stat keys, `_validate_stats` will reject it and the eval will fail to start.

**Validation:** Run eval; confirm seed loads without validation error. Total of 11 is within valid range (8–12).

---

#### Step 1.11 — Update conftest.py test fixtures

**File:** `tests/conftest.py`

**What:** Remove `lore` and `resolve` from any hardcoded stats dicts in test fixtures.

**Why:** Fixtures with 6-skill stat dicts will fail `_validate_stats` after the change.

**Code Snippet**

Find the fixture stats dict:
```python
"stats": {"strength": 3, "dexterity": 2, "wits": 1, "lore": 1, "charisma": 1, "resolve": 1}
```
Replace with:
```python
"stats": {"strength": 3, "dexterity": 2, "wits": 1, "charisma": 1}
```

**Validation:** Confirm no remaining references to lore or resolve in conftest.py.

---

#### Step 1.12 — Update repomap documentation

**File:** `docs/repomap.md`

**What:** Update the `SkillName` entry in the Type aliases table and the `pc.stats` entry in the State shape section.

**Why:** Repomap is the canonical reference. Stale entries mislead the execution model on future tasks.

**Code Snippet**

Type aliases table — find:
```
| `SkillName` | 6 skills (strength, dexterity, wits, lore, charisma, resolve) |
```
Replace with:
```
| `SkillName` | 4 skills (strength, dexterity, wits, charisma) |
```

State shape section — find:
```
stats: {strength, dexterity, wits, lore, charisma, resolve}: int (1-4 each, total 12-16)
```
Replace with:
```
stats: {strength, dexterity, wits, charisma}: int (1-4 each, total 8-12)
```

**Validation:** Read both sections; confirm no lore or resolve remain. Total range updated to 8–12.

---

### Tests to write or update
Tests are temporarily disabled per AGENTS.md. No test changes required beyond the conftest.py fixture update in Step 1.11.

---

### REPOMAP and architecture updates
- `docs/repomap.md` — Type aliases table (`SkillName`) and State shape `pc.stats` block (Step 1.12 above).

---

### Risks

1. **Archetype preset totals.** After removing lore and resolve, archetype stat values must be redistributed to stay within the new 8–12 total range. Warrior (3-4-2-2=11) and scout (2-4-3-2=11) are valid; scholar (2-2-4-3=11), charmer (2-2-2-4=10), survivor (3-3-2-2=10) also valid. If any archetype total falls outside 8–12, the UI will reject it on character creation.

2. **Dynamic pack seeds.** LLM-generated seeds (via `generate_seed_system.j2`) may still emit lore/resolve if the prompt update in Step 1.5 is incomplete or the model ignores it. The `_validate_stats` check will catch this at seed application time and return an error. Monitor first dynamic pack generation after deploy.

3. **Existing save files.** Any saved game state on disk with lore/resolve stats loaded via YAML will bypass `_validate_stats`. The engine may crash when accessing `pc.stats["lore"]` or similar keys in condition modifiers. This is acceptable — old saves become incompatible, which is expected behavior for a skill-system change.

---

