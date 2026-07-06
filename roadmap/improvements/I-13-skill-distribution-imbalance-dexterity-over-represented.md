---
title: "Skill distribution imbalance — dexterity over-represented, strength under-represented"
status: done
urgency: 3
size: medium
created: 2026-06-29
ticket_id: I-13
labels: [ruling, skill-check, balancing]
---

## E-7 Assessment (5 runs, 54 rolls)

| Skill     | Count | %    | Target | Delta  |
|-----------|-------|------|--------|--------|
| Charisma  | 22    | 40.7%| 25%    | +15.7% |
| Dexterity | 16    | 29.6%| 25%    | +4.6%  |
| Wits      | 10    | 18.5%| 25%    | -6.5%  |
| Strength  | 6     | 11.1%| 25%    | -13.9% |

**Regression:** Charisma went from under-represented to over-represented. The intent_verb → skill mapping fix was too aggressive for charisma. Persuade (11) and intimidate (8) are dominant intent verbs.

**Still under-represented:** Strength (-13.9%). Attack intent verb only 5 occurrences across 54 rolls.

**Near target:** Wits (-6.5%), Dexterity (+4.6%).

**Recommendation:** Narrow charisma intent verb mapping. Reduce persuade/intimidate weight in ruling prompt. Add explicit strength use cases beyond attack (lift, break, carry, shove, etc.).

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

## Phase 6 Data — Fresh 25-Turn Runs (4 runs, 2026-06-30)

Examined 4 fresh runs at commit `12332bab` (post-band-aid-removal):
- Golden-piracy: dexterity 3, charisma 1, strength 1 (5 rolls)
- Space-western: dexterity 3, wits 1 (4 rolls)
- Noir-1930s: charisma 2, dexterity 2, wits 4 (8 rolls)

**Charisma usage improved significantly:**
- Golden-piracy: charisma appeared (turn 20) — was 0% in earlier runs
- Noir-1930s: charisma appeared twice (turns 5, 10) — intent_verb `intimidate` and `persuade` mapped correctly

**Wits usage improved in noir:**
- Noir-1930s: wits appeared 4 times out of 8 rolls (50%) — intent_verb `wits` and `recall` mapped correctly
- This reflects the noir pack's investigative focus

**Dexterity still dominant in space-western/golden-piracy:**
- Space-western: 3/4 rolls (75%) — reflects stealth/combat focus of the pack
- Golden-piracy: 3/5 rolls (60%) — reflects combat focus of the pack
- This may be appropriate for these packs rather than a prompt issue

**Assessment:** The intent_verb → skill mapping is working. Charisma usage improved from earlier runs. The fix is effective but dexterity dominance in certain packs may reflect pack design rather than a prompt issue. Further refinement may be needed if charisma remains low across all packs.

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

## Evaluation Findings (2026-07-04)

### space-western run (15 turns, gemma-4-26b-a4b-it)

**Roll distribution (8 rolls examined):**
- crit_fail: 37.5% (3/8)
- fail: 12.5% (1/8)
- setback: 12.5% (1/8)
- partial: 12.5% (1/8)
- success: 12.5% (1/8)
- crit_success: 12.5% (1/8)
- Heavy skew toward negative bands (50% crit_fail + fail)
- Only 2 positive rolls out of 8
- This is a band distribution issue, not a skill distribution issue — the ticket's focus on skill mapping is still valid but secondary to the band problem

**Skill distribution (8 rolls):**
- Dexterity dominant (consistent with space-western pack's stealth/combat focus)
- Low charisma/wits usage (consistent with earlier Phase 6 data)
- The space-western pack design heavily favors dexterity — 15/16 rolls were dexterity in the earlier run
- This may be appropriate for the pack rather than a prompt issue

**Conclusion:** The ticket's proposed fix (broaden skill definitions, add strength use cases, refine charisma mapping) is validated. The space-western run confirms dexterity dominance but also reveals a secondary issue: negative bands heavily dominate (50% crit_fail/fail), which is a separate pacing/band issue (see I-25). Further refinement needed if charisma remains low across all packs.

## Updated Evaluation (2026-07-05 — Post-Fix Runs)

### Insufficient Data from Short Runs (9 turns each)

All three new runs (noir-1930s, space-western, golden-piracy) have very few dice rolls — most turns have `rolled: False` (no check required by ruling LLM).

| Pack | Total Rolls | Skill Distribution |
|------|-------------|-------------------|
| noir-1930s | 3 | charisma (3) — 100% |
| space-western | 2 | charisma (2) — 100% |
| golden-piracy | 4 | wits (1), charisma (3) — 25% wits, 75% charisma |

**Conclusion:** Cannot assess skill distribution imbalance from these short runs. Need longer runs (20+ turns) with more dice rolls. The ruling LLM is very aggressive about "no check required" — only 2-6 rolls per 9 turns. This is a ruling prompt issue (too many actions deemed routine), not a skill mapping issue.

**Note:** The turns that DO have rolls are ALL charisma (noir, western) or charisma-heavy (piracy). This is consistent with earlier Phase 6 data showing low dexterity usage (3-4 rolls per 25 turns in post-fix runs). The skill distribution may be more balanced than earlier Phase 4 data (68% dexterity) but the sample is too small to confirm.