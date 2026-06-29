---
title: "Skill distribution imbalance — dexterity over-represented, strength under-represented"
status: new
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

## Intent Verb Distribution (86 checks)

| Verb | Count | % |
|------|-------|---|
| sneak | 24 | 28.0% |
| attack | 17 | 20.0% |
| escape | 14 | 16.3% |
| recall | 14 | 16.3% |
| persuade | 8 | 9.3% |
| intimidate | 3 | 3.5% |

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

- F-4: Balancing charisma bias in rulings (design doc, status: testing)
- I-4: Balancing difficulty — too many hard rolls
- Phase 2 data showed dexterity 49%, charisma 20% — dexterity improved from 49% to 58% after I-11 changes

## Files to Review

- `ccya/prompts/ruling_system.j2` — skill definitions, intent verb routing
- `ccya/prompts/ruling_user.j2` — skill check guidance
- `ccya/engine/ruling.py` — skill assignment logic
- `ccya/prompts/world_system.j2` — beat types and skill opportunities
- `evals/scenarios/` — pack scenarios for skill distribution analysis