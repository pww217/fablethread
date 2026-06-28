# Consolidated Eval Report

**Group:** `2026-06-27_0.30.0-28-g0d8013d5_0d8013d`
**Date:** 2026-06-27
**SHA:** 0d8013d
**Prior SHA:** 959704f
**Runs:** 3 (noir-1930s/driven, allied-ww2/aggressive, zombie-survival/cautious)
**Turns:** 15 each

---

## 1. Changes Since Last Eval

One commit between prior eval and current:

- `[simplify-beat-pipeline]` — Switch ruling to index-based beat selection, remove npc_id/driver from beat pipeline
- `prompt fixes: driver constraint in ruling, diversity hard rules in world, eval findings doc`

The beat pipeline simplification is the primary change to review against pacing/convergence behavior.

---

## 2. Testing Items

No bugs with `status: testing` found. Nothing to assess.

---

## 3. Checker Scores

| Area | Noir (driven) | Allied (aggressive) | Zombie (cautious) |
|------|:---:|:---:|:---:|
| Ruling | 2/2 PASS | 2/2 PASS | 2/2 PASS |
| Narration | 0/0 SKIP | 0/0 SKIP | 0/0 SKIP |
| Pacing | 3/5 FAIL | 4/5 FAIL | 4/5 FAIL |
| State | 5/5 PASS | 5/5 PASS | 5/5 PASS |
| Threads | 4/4 PASS | 4/4 PASS | 4/4 PASS |
| Arcs | 3/3 PASS | 3/3 PASS | 3/3 PASS |
| NPCs | 2/2 PASS | 2/2 PASS | 2/2 PASS |
| GM Beats | 2/2 PASS | 2/2 PASS | 2/2 PASS |
| Rolls | 1/1 PASS | 1/1 PASS | 1/1 PASS |
| **Overall** | **23/25 (92%)** | **23/25 (92%)** | **24/25 (96%)** |

### Failures by run:

**Noir (driven) — 92%:**
- `phase_transition`: CLIMAX at turn 8 with `climax_turn_count=4 >= limit` but `outcome_hint='advance'` (expected `'transition'`)
- `convergence_components`: RISING→CLIMAX at turn 5 with score 2 < threshold 3; RISING→CLIMAX at turn 15 with score 2 < threshold 3

**Allied (aggressive) — 92%:**
- `convergence_components`: RISING→CLIMAX at turn 11 with score 2 < threshold 3
- `extraction_retry_rates`: State extraction required 2 retries on turns 13 and 15 — `condition_change_reason is required when condition changes are present`

**Zombie (cautious) — 96%:**
- `phase_transition`: CLIMAX at turn 7 with `climax_turn_count=4 >= limit` but `outcome_hint='hold'` (expected `'transition'`)

---

## 4. Phase Transition Analysis

### Noir (driven)
```
Turn 3:  SETUP → RISING        (score=1, advance)
Turn 5:  RISING → CLIMAX       (score=2, advance) ← below threshold 3
Turn 10: CLIMAX → RESOLUTION   (score=2, transition)
Turn 11: RESOLUTION → BREATHER (score=2, breather)
Turn 13: BREATHER → RISING     (score=0, advance)
Turn 15: RISING → CLIMAX       (score=2, transition) ← below threshold 3
```
**Issues:** Early RISING→CLIMAX at turn 5 with score 2 (threshold is 3). Final RISING→CLIMAX at turn 15 also below threshold. CLIMAX phase held too long (turns 5-9, 5 turns) without forced transition at turn 8.

### Allied (aggressive)
```
Turn 3:  SETUP → RISING        (score=3, advance)
Turn 4:  RISING → CLIMAX       (score=4, advance)
Turn 9:  CLIMAX → RESOLUTION   (score=3, transition)
Turn 10: RESOLUTION → BREATHER (score=3, hold)
Turn 12: BREATHER → RISING     (score=2, advance)
Turn 13: RISING → CLIMAX       (score=3, hold)
```
**Issues:** RISING→CLIMAX at turn 11 with score 2 < threshold 3. Otherwise clean pacing.

### Zombie (cautious)
```
Turn 3:  SETUP → RISING        (score=3, advance)
Turn 4:  RISING → CLIMAX       (score=4, advance)
Turn 9:  CLIMAX → RESOLUTION   (score=3, transition)
Turn 10: RESOLUTION → BREATHER (score=3, hold)
Turn 12: BREATHER → RISING     (score=2, advance)
Turn 13: RISING → CLIMAX       (score=3, hold)
```
**Issues:** CLIMAX at turn 7 with `climax_turn_count=4 >= limit` but `outcome_hint='hold'` — should have been forced to transition.

---

## 5. Extraction Warnings

### Noir (driven)
- No extraction retries. Clean extraction.
- Thread dedup: 2 rejected (T4 missing_evidence 0.71x, T15 judicial_corruption 0.74x) — normal overlap rejection.

### Allied (aggressive)
- **State extraction retries on turns 13 and 15:** `condition_change_reason is required when condition changes are present`. The LLM is adding conditions without providing the required `condition_change_reason` field. This is a prompt/model issue — the state extractor template needs to enforce this constraint more clearly.
- Thread dedup: 6 rejected (T2, T3, T4 enemy_encroachment; T6 internal_hostility; T10 mysterious_stranger; T12, T15 supply_diversion_route) — high dedup rate suggests thread fragmentation or overly broad thread names.

### Zombie (cautious)
- No extraction retries. Clean extraction.
- Thread dedup: 2 rejected (T2 supply_corruption 1.0x, T10 security_detection 0.79x) — normal.

---

## 6. Inventory Canonical ID Warnings

Multiple `resolve_inventory_canonical_id no match` warnings across all runs:
- **Noir:** `case_dismissal_files`, `arrest_files`, `leather_bound_ledger`
- **Allied:** `family_letters`, `service_pistol`, `redacted_parchment`, `leather_satchel`, `small_arms_ammo`/`small_arms_ammunition`
- **Zombie:** `data_slate`, `medical_canister`, `militia_manifest`

These indicate inventory items being added to the game state that don't have canonical IDs registered in the inventory system. The items are still being tracked (they appear in deltas) but the canonical resolution is failing. This is a data quality issue — inventory definitions in the packs need to include these items.

---

## 7. New Bugs Found

### Bug: State extraction fails when LLM adds conditions without condition_change_reason
- **Runs affected:** Allied (turns 13, 15)
- **Error:** `EXTRACTION_COERCION_FAILED: condition_change_reason is required when condition changes are present`
- **Impact:** State extraction retries, increased latency, potential state loss on retry failure
- **Root cause:** State extractor prompt/template not enforcing `condition_change_reason` as required when conditions are added/changed

### Bug: Phase transition forced at climax_turn_count limit but model ignores it
- **Runs affected:** Noir (turn 8), Zombie (turn 7)
- **Issue:** `climax_turn_count >= limit` but `outcome_hint` is `advance`/`hold` instead of `transition`
- **Impact:** CLIMAX phase can stretch beyond intended duration, pacing drifts
- **Root cause:** The `outcome_hint` is generated by the LLM (narrate/record step) and can ignore the pacing system's expectation. The ruling or pacing system should enforce the transition rather than rely on the model's `outcome_hint`.

### Bug: Convergence score threshold too low for RISING→CLIMAX transitions
- **Runs affected:** Noir (turns 5, 15), Allied (turn 11)
- **Issue:** RISING→CLIMAX transitions occurring at score 2 when threshold is 3
- **Impact:** Premature CLIMAX entries, compressed pacing
- **Root cause:** Either the convergence score calculation is not accumulating enough components, or the threshold is too high for the current beat pipeline design.

### Bug: Inventory canonical ID resolution failing for pack-specific items
- **Runs affected:** All 3 runs
- **Issue:** `resolve_inventory_canonical_id no match` for multiple items per pack
- **Impact:** Items tracked but not canonicalized; potential downstream issues with inventory checkers
- **Root cause:** Pack definitions missing canonical inventory entries for items the game generates

---

## 8. Recommendations

1. **Fix state extractor prompt** — Add `condition_change_reason` as a required field when conditions change. This is the highest-impact fix (allied run had 2 retries).

2. **Enforce phase transitions at the engine level** — Don't rely on `outcome_hint` from the LLM to enforce CLIMAX transitions. The pacing system should force the transition when `climax_turn_count >= limit`.

3. **Review convergence score calculation** — Score 2 triggering RISING→CLIMAX suggests either the threshold (3) is too high or the score components aren't accumulating correctly with the new index-based beat pipeline.

4. **Register missing inventory canonical IDs** — Add canonical entries for all items appearing in pack definitions to eliminate `resolve_inventory_canonical_id no match` warnings.

5. **Investigate thread dedup rate in allied run** — 6 thread rejections vs 2 in other runs suggests thread fragmentation or overly broad thread naming in the allied-ww2 pack.
