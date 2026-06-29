---
title: "[Balancing] Charisma bias in rulings — analyze ratio"
status: testing
urgency: 3
size: small
created: 2026-06-12
ticket_id: F-4
labels:
  - Improvement
  - Balancing
---

## Detail

Games feel overly biased towards charisma. Most turns involve talking, so charisma is used most frequently. Dex is second, then strength and wits. Need to analyze the ratio and balance.

## Scope

* Gather evidence: analyze skill usage ratios across recent sessions
* Check if ruling extractor over-weights social intent verbs
* Review if difficulty assignment favors social rolls
* Consider: difficulty assignment, ruling extraction, or prompt bias?
* Balance may require adjusting any of the above

## Files

* `ccya/engine/extraction.py` — ruling extraction (intent verb → skill mapping)
* `ccya/rules.py` — difficulty assignment
* `ccya/prompts/` — ruling extraction prompts

## Resolution

Analyzed 50 runs (470 skill checks) across evals. Found dexterity at 49%, strength 23%, charisma 20%, wits 9%. Root cause: skill definitions in ruling prompt were too narrow — wits had no guidance for observation/analysis/search actions, dexterity had vague "fine motor" catch-all. Fixed by rewriting the 4 skill definitions in `ruling_system.j2` to be more explicit and balanced. Also simplified intent_verb guidance to remove false precision (verb only used as decorative prefix on setback/partial directive text).

## Verification (Phase 3, 2026-06-29)

Analyzed 5 games × 25 turns = 125 turns, 86 skill checks.

**Current distribution:**
- dexterity: 58.1% (50 checks) — sneak 22, attack 16, escape 9
- wits: 20.9% (18 checks) — recall 7, hack 3, escape 3, sneak 3
- charisma: 14.0% (12 checks) — persuade 8, intimidate 4
- strength: 7.0% (6 checks) — attack 5, escape 1

**Charisma improved from 20% → 14%.** Wits improved from 9% → 20.9%. Dexterity increased slightly (49% → 58.1%) due to action-heavy packs. Strength decreased (23% → 7%) — may need review.

**Difficulty distribution:** hard 51.2%, normal 47.7%, easy 1.2%. Very high difficulty rate — most checks are hard or normal.

**Intent verb distribution:** sneak 28.0%, attack 20.0%, escape 16.8%, recall 16.8%, persuade 9.6%, intimidate 4.0%. Charisma intent verbs (persuade + intimidate) total 13.6%.

## Remaining Work

Target is ~25% per skill. Current gap:
- dexterity is over-represented (58% vs 25% target)
- strength is under-represented (7% vs 25% target)
- charisma is close but still low (14% vs 25% target)
- wits is near target (21% vs 25% target)

**Possible causes:**
1. Skill definitions in `ruling_system.j2` may still favor dexterity — dexterity covers "agility, stealth, ranged attacks, fine motor, dodge, pickpocket" which is broad
2. Pack design may favor stealth/combat over brute force/social scenarios
3. Intent verb mappings may route too many actions to dexterity
4. Difficulty assignment may bias toward dexterity checks

**Need to investigate:**
- Review skill definitions in `ruling_system.j2` lines 6-9
- Check intent verb → skill mapping logic in `ccya/engine/extraction.py`
- Analyze if specific packs (space-western, zombie-survival) skew dexterity
- Consider narrowing dexterity definition or adding guidance to use other skills more
- Consider if strength needs broader definition (currently "Physical force, melee, lifting, breaking, enduring pain")
