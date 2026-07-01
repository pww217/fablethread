---
title: "Skill distribution imbalance — dexterity over-represented, strength under-represented"
status: testing
urgency: 3
size: medium
created: 2026-06-29
ticket_id: I-13
labels: [ruling, skill-check, balancing]
---

## Description

Skill distribution in rulings is heavily skewed toward dexterity. Target is ~25% each across dexterity, strength, charisma, wits. Phase 3 data (86 checks) shows dexterity 58.1%, wits 21%, charisma 14%, strength 7%.

## Phase 3 Data (86 checks across 5 games)

| Skill | Target | Actual | Delta |
|-------|--------|--------|-------|
| Dexterity | 25% | 58.1% | +33.1% |
| Wits | 25% | 21% | -4% |
| Charisma | 25% | 14% | -11% |
| Strength | 25% | 7% | -18% |

## Phase 4 Data — 25-Turn Runs (50 checks across 3 games)

| Skill | Target | Actual | Delta |
|-------|--------|--------|-------|
| Dexterity | 25% | 68.0% | +43.0% |
| Strength | 25% | 16.0% | -9.0% |
| Charisma | 25% | 12.0% | -13.0% |
| Wits | 25% | 4.0% | -21.0% |

Breakdown by run:
- Golden-piracy: charisma 3, strength 7, dexterity 9 (19 rolls)
- Space-western: dexterity 15, strength 1 (16 rolls)
- Noir-1930s: dexterity 10, charisma 3, wits 2 (15 rolls)

Dexterity worsened from 58.1% to 68.0%. Wits collapsed from 21% to 4%. Charisma stayed low at 12%. Strength improved slightly from 7% to 16% but still far below target. The space-western run is extreme — 15 out of 16 rolls are dexterity.

## Phase 5 Data — Skill Distribution Fix Applied (2026-06-30)

Fix applied: Narrowed dexterity definition in `ruling_system.j2:5-9`, added explicit guidance for charisma/wits/strength, added intent_verb → skill mapping. `recent_beats_max` fixed in `config.yaml` from 5 to 10.

Space-western run (25 turns): wits 40%, dexterity 40%, charisma 4%, ?: 2. Much better balance than Phase 4! The intent_verb → skill mapping is working. Charisma improved from 0% to 4% in this run. Dexterity still dominant but much less extreme.

Note: This run used the updated ruling prompt. The skill distribution is much improved but charisma is still low. The fix is working but may need further refinement.

## Investigation Update (2026-06-30)

prepare_seed temperature was lowered from 0.4 to 0.2 to fix intermittent JSON output failures. Note: this only affects initial seed generation, not ruling. Ruling already has temperature 0.2. The skill distribution fix (narrowed dexterity, intent_verb → skill mapping) should be tested with fresh runs at the ruling temperature. The prepare_seed fix didn't solve the problem — still getting failures at 0.2 (2 out of 13 calls). The issue is in the LLM output format, not temperature.

## Intent Verb Distribution (86 checks)

| Verb | Count | % |
|------|-------|---|
| sneak | 24 | 28.0% |
| attack | 17 | 20.0% |
| escape | 14 | 16.3% |
| recall | 14 | 16.3% |
| persuade | 8 | 9.3% |
| intimidate | 3 | 3.5% |

**Charisma intent verbs (persuade + intimidate) total 13.6%.** Social interactions are rare.

## Difficulty Distribution (86 checks)

| Difficulty | Count | % |
|------------|-------|---|
| Hard | 44 | 51.2% |
| Normal | 41 | 47.7% |
| Easy | 1 | 1.2% |

Very high difficulty rate — most checks are hard or normal. Only 1.2% easy.

## Root Causes

### Narrow dexterity definition in ruling prompt
- `sneak`, `escape`, and many stealth/combat actions map to dexterity
- Intent verb routing may over-count dexterity
- Pack design may favor stealth/combat scenarios

### Charisma under-represented
- `persuade` and `intimidate` are rare intent verbs (12.8% combined)
- Social interactions may not be triggering skill checks often enough
- World step may not create enough social pressure beats

### Strength under-represented
- `attack` maps to strength but only 20% of checks
- Combat may be resolved without skill checks (ruling "no check required")
- Strength checks may be conflated with dexterity in ruling prompt

## Fix Needed

### Ruling prompt
- Review and broaden skill definitions in ruling prompt
- Ensure strength has clear use cases beyond attack
- Add guidance for social skill checks (charisma)
- Consider intent verb to skill mapping

### Pack design
- Review pack scenarios for skill distribution bias
- Ensure packs create opportunities for all 4 skills
- Consider adding skill-balanced beat types

### World step
- Add guidance to create social pressure beats (charisma opportunities)
- Add guidance to create physical challenge beats (strength opportunities)
- Consider skill-balanced beat types in world step

## Related

- F-4: Charisma bias in rulings — superseded by this ticket (consolidated)
- I-4: Balancing difficulty — too many hard rolls
- Phase 2 data showed dexterity 49%, charisma 20% — dexterity improved from 49% to 58% after I-11 changes

## Files to Review

- `ccya/prompts/ruling_system.j2` — skill definitions, intent verb routing
- `ccya/prompts/ruling_user.j2` — skill check guidance
- `ccya/engine/ruling.py` — skill assignment logic
- `ccya/prompts/world_system.j2` — beat types and skill opportunities
- `evals/scenarios/` — pack scenarios for skill distribution analysis