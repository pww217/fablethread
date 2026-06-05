# Cut Skill System to Four Core Skills

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Remove lore and resolve | Delete both skills from all code, prompts, UI, and docs |

## Objective
The current 6-skill system includes `lore` and `resolve` which never appear in practice — eval runs consistently flag them as missing across full play sessions. Both skills lack a distinct active-verb domain: lore overlaps wits (cognition), and resolve overlaps the existing physical/social skills (endurance already covered by strength/dexterity, social resistance by charisma). Cutting to the four genuinely distinct skills (strength, dexterity, wits, charisma) eliminates dead stat weight and stops the eval coverage gap flag from firing on a structural limitation rather than a real problem.

## Non-goals
- Does not rename or redefine any remaining skill.
- Does not change the dice resolution logic in `rules.py` beyond the skill set constant.
- Does not migrate existing save files — no backward compatibility required per AGENTS.md.
- Does not change stat point allocation totals or the 1–4 range per skill.
- Does not update any eval scenario seed that hardcodes lore/resolve stat values — those are handled implicitly (see Risks).

---

## Implementation — Phase 01: Remove lore and resolve

### Files to pull for context
- `ccya/models.py`
- `ccya/rules.py`
- `ccya/server/app.py`
- `ccya/prompts/ruling_system.j2`
- `ccya/prompts/generate_seed_system.j2`
- `ccya/templates/index.html`
- `evals/rubrics/narrative_interplay.md`
- `ccya/eval/engine_mirror.py`
- `evals/scenarios/eval_coverage_gap.py`
- `evals/packs/eval-pack/seed_state.yaml`
- `tests/conftest.py`
- `docs/repomap.md`

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
    return True
```

**Validation:** Submit a new-game request via curl with only 4 stats; confirm 200. Submit with lore/resolve; confirm 422.

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

**Validation:** Generate a new seed and confirm the resulting `state.yaml` has exactly 4 stat keys.

---

#### Step 1.6 — Update character creation UI

**File:** `ccya/templates/index.html`

**What:** Remove the `lore` and `resolve` entries from the `skills` array in the Vue/Alpine data block.

**Why:** The UI renders a stat allocation widget per skill entry. Dead skills must not appear in character creation.

**Code Snippet**

Remove these two objects from the skills array:
```js
{ key: 'lore', label: 'Lore', description: 'Knowledge, investigation, and recalling information.', value: 2 },
{ key: 'resolve', label: 'Resolve', description: 'Mental fortitude, resisting fear, and pushing through pain.', value: 2 },
```

The remaining array should be:
```js
{ key: 'strength', label: 'Strength', description: '...', value: 2 },
{ key: 'dexterity', label: 'Dexterity', description: '...', value: 2 },
{ key: 'wits', label: 'Wits', description: 'Awareness, perception, and quick thinking under pressure.', value: 2 },
{ key: 'charisma', label: 'Charisma', description: 'Persuasion, leadership, and reading people.', value: 2 },
```

**Validation:** Load character creation page; confirm only 4 stat sliders appear. Confirm total stat budget logic still functions (point buy or fixed — verify the `total` getter if present still computes correctly with 4 skills).

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

#### Step 1.10 — Update eval pack seed state

**File:** `evals/packs/eval-pack/seed_state.yaml`

**What:** Remove `lore` and `resolve` keys from `pc.stats`.

**Why:** The eval pack seed is loaded directly into the engine at eval time. If it contains invalid stat keys, `_validate_stats` will reject it and the eval will fail to start.

**Code Snippet**
```yaml
stats:
  strength: 3
  dexterity: 3
  wits: 2
  charisma: 3
```

Note: the original total was 16 (3+3+2+2+3+3). Dropping lore (2) and resolve (3) removes 5 points. Redistribute or accept the lower total — confirm the engine does not enforce a specific total, only the 1–4 per-skill range and correct key set. If a total constraint exists, adjust values to compensate.

**Validation:** Run eval; confirm seed loads without validation error.

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
stats: {strength, dexterity, wits, charisma}: int (1-4 each)
```

**Validation:** Read both sections; confirm no lore or resolve remain.

---

### Tests to write or update
Tests are temporarily disabled per AGENTS.md. No test changes required beyond the conftest.py fixture update in Step 1.11.

---

### REPOMAP and architecture updates
- `docs/repomap.md` — Type aliases table (`SkillName`) and State shape `pc.stats` block (Step 1.12 above).

---

### Risks

1. **Stat total constraints in UI.** The character creation UI may enforce a fixed point budget. With 4 skills at default value 2, the starting total is 8. If the UI's `total` getter or min/max logic was calibrated for 6 skills, the budget may need adjustment. Read the `total` getter before committing Step 1.6.

2. **Existing save files.** Any saved game state on disk will have lore and resolve in `pc.stats`. The engine will load them without error (YAML load is permissive) but `_validate_stats` is only called at new-game time, not on load — so running saves are unaffected. No migration needed.

3. **Dynamic pack seeds.** LLM-generated seeds (via `generate_seed_system.j2`) may still emit lore/resolve if the prompt update in Step 1.5 is incomplete or the model ignores it. The `_validate_stats` check will catch this at seed application time and return an error. Monitor first dynamic pack generation after deploy.

4. **eval-pack seed total.** Original eval seed total was 16. After removing lore (2) and resolve (3), total drops to 11. Verify the engine has no minimum total enforcement — if it does, bump one stat to compensate.

---

## Ambiguities requiring resolution before execution

1. **Stat point budget in character creation UI.** Does the UI enforce a minimum or maximum total across all skills? If yes, what should the new target total be for 4 skills? Options: A) Keep current per-skill defaults (4 × 2 = 8 total, no budget enforcement change needed) B) Adjust budget cap to a new value appropriate for 4 skills.
