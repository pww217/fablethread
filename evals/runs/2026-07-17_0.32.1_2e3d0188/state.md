# State Review Report

**Eval group:** `evals/runs/2026-07-17_0.32.1_2e3d0188/`
**Date:** 2026-07-18
**Mechanics reviewed:** location_change, location_description_consistency, inventory_integrity, conditions_lifecycle, condition_ttl, world_state_facts, world_state_ttl, roll_band_consistency

---

## 1. Mechanic Overview

State mechanics govern the game world's persistent data: location tracking and descriptions, inventory management, condition lifecycle and TTL, world state facts and their TTL, and roll band consistency. These are the backbone of game state integrity — failures here corrupt the game state that persists across turns and shapes all downstream mechanics.

---

## 2. Runs Examined + Turns Sampled

**Runs examined (5 of 6 listed — space-western:explorer 25t directory missing from disk):**

| Pack | Persona | Turns | Checkers |
|------|---------|-------|----------|
| noir-1930s | driven | 25 | 42/43 PASS (97.7%) |
| space-western | speedrunner | 25 | 43/43 PASS (100%) |
| golden-piracy | completionist | 25 | 43/43 PASS (100%) |
| zombie-survival | cautious | 25 | 43/43 PASS (100%) |
| allied-ww2 | aggressive | 25 | 43/43 PASS (100%) |

**Turns sampled per mechanic:**
- location_change: All turns with `applied.location_change` present (8, 8, 4, 4, 6 changes across runs)
- location_description_consistency: All 25 turns per run (post-turn state)
- inventory_integrity: All turns with inventory changes (16, 12, 7, 6, 17 changes)
- conditions_lifecycle: All turns with condition changes (7, 8, 10, 11, 15 changes)
- condition_ttl: Conditions tracked across turns where TTL should decrement (T12-T25 in zombie-survival, T10-T25 in noir-1930s)
- world_state_facts: T1, T10, T20, T25 per run
- world_state_ttl: Facts with `expires_turn` and `permanent` fields across T1-T25
- roll_band_consistency: All 22-25 rolls per run

---

## 3. Findings

### 3.1 location_change — PASS

All 5 runs pass the `location_change` checker. Location changes are correctly emitted in the State extractor (not the Scene extractor as the CHECKERS.md doc implies — see §7). Post-turn location ID differs from previous turn's location ID on every change.

**Examples:**
- noir-1930s T4: `rusty_anchor_tavern` → `land_commission_office`
- space-western T3: `marketplace` → `logistics_office`
- zombie-survival T7: `warehouse_foundation` → `farmhouse_ruins`

**Note:** The CHECKERS.md doc at line 45 says "Only checks turns where `applied.location_change` is present" and references `extraction_context` as not stored. This is accurate — the checker reads from `applied.location_change` in events.

### 3.2 location_description_consistency — PASS (with concern)

All 5 runs pass the `location_description_consistency` checker. However, **every single location description across all 5 runs is under 30 words** (12-19 words typical). The checker passes because it uses OR logic: fail only if `words < 15 AND sentences < 1`. Since all descriptions have at least 1 sentence, they pass even though they're clearly too short.

**Examples (all under 30 words):**
- noir-1930s: "A rowdy, dim tavern smelling of gin and sawdust, located near the city docks." (14w)
- space-western: "A cramped, oily, and dark network of conduits running through the station's infrastructure." (13w)
- golden-piracy: "A small, isolated rock ledge tucked deep within the damp, dark interior of a sea cave." (16w)
- zombie-survival: "A narrow, muddy path winding through the belly of a steep valley, flanked by brambles and obstructed..." (19w)
- allied-ww2: "A wide, desolate stretch of beach exposed to the wind and crashing surf." (13w)

**Checker threshold:** `location_min_words=15`, `location_min_sentences=1`. The OR logic means descriptions with 1+ sentence pass even if under 15 words.

### 3.3 inventory_integrity — PASS

All 5 runs pass. No negative inventory amounts, no overdraw, no removal of non-existent items. Inventory changes are clean across all runs.

**Examples of clean operations:**
- noir-1930s T2: Add `folded_newspaper` + `napkin`, no removes
- allied-ww2 T1: Add `intelligence_documents`, remove `medical_kit`, update `m1_garand`
- golden-piracy T18: Remove `flintlock_pistol` (previously added at T3)

### 3.4 conditions_lifecycle — PASS

All 5 runs pass the `conditions_lifecycle` checker. Condition IDs appear in ruling reasons, no duplicate IDs.

**Notable:** zombie-survival run has condition IDs with inconsistent casing (`rattled` lowercase vs `Rattled` in other runs). This doesn't break the checker (case-insensitive comparison) but is worth noting.

### 3.5 condition_ttl — FAIL (Critical Bug)

**All 5 runs fail this mechanic.** TTL is NOT decrementing on existing conditions. This is a critical bug in `_expire_conditions()` in `ccya/engine/turn_state.py:443`.

**Root cause:** The function at line 443 has `if not isinstance(c, dict): continue`. The `state.pc.conditions` list contains `Condition` model objects (not dicts), so ALL conditions are skipped by this check. The TTL decrement code at lines 449-460 is dead code — it never executes.

**Evidence (zombie-survival):**
- `rattled` added at T13 with `turns_remaining: 10`. Stays at 10 through T24 (11 turns, should be 10,9,8,7,6,5,4,3,2,1,0,expired).
- `exhausted` added at T12 with `turns_remaining: 3`. Stays at 3 through T24 (12 turns, should be 3,2,1,0,expired,0,0,0,0,0,0,0).
- `focused` added at T21 with `turns_remaining: 2`. Stays at 2 through T24 (3 turns, should be 2,1,0,expired).

**Evidence (noir-1930s):**
- `cornered` added at T10 with `turns_remaining: 2`. Stays at 2 through T15 (5 turns, should be 2,1,0,expired,expired,expired).

**Impact:** Conditions persist indefinitely instead of expiring. This breaks the condition lifecycle entirely — conditions never expire via TTL, only via explicit removal. This affects game balance, narrative tension, and the condition checker's expectations.

### 3.6 world_state_facts — PASS

All 5 runs pass. World state facts are all substantive (52-126 chars, well above the 10-char minimum). Facts are mostly static seed data with occasional additions from thread resolution.

**Examples:**
- noir-1930s: 5 facts, all 77-126 chars, static across T1-T25
- golden-piracy: 3 static + 2 dynamic facts at T25
- allied-ww2: 5 static + 2 dynamic facts at T25

### 3.7 world_state_ttl — PASS

All 5 runs pass. Facts with `expires_turn` are correctly tracked. In golden-piracy T25, two facts have `expires_turn=28` and `expires_turn=30` — both still present since we're only at turn 25. No TTLs have expired yet in any run.

**Fact structure:** `{"id": "...", "text": "...", "tier": "global"/"local", "valence": "...", "permanent": true/false, "expires_turn": int|null}`

### 3.8 roll_band_consistency — PASS

All 5 runs pass. Dice rolls match their assigned bands correctly. Roll distribution varies by run but is within reasonable bounds:

| Run | Rolls | crit_fail | fail | setback | partial | success | crit_success |
|-----|-------|-----------|------|---------|---------|---------|--------------|
| noir-1930s | 22 | 0 | 4 | 3 | 1 | 9 | 5 |
| space-western | 18 | 1 | 7 | 0 | 2 | 5 | 3 |
| golden-piracy | 22 | 0 | 7 | 0 | 0 | 6 | 9 |
| zombie-survival | 22 | 0 | 5 | 0 | 2 | 10 | 5 |
| allied-ww2 | 25 | 1 | 7 | 4 | 2 | 7 | 4 |

---

## 4. Cross-Run Patterns

**Consistent issues across all runs:**
1. **condition_ttl never decrements** — This is the single most critical finding. The bug is in `turn_state.py:443` and affects all runs identically.
2. **Location descriptions consistently short** — All descriptions are 12-19 words, well below the 30-word threshold. The checker's OR logic masks this issue.

**Run-specific observations:**
- noir-1930s: Highest number of location changes (8), condition casing inconsistency (`cornered` vs `Cornered`)
- space-western: Most rolls (18), highest fail rate (38.9%)
- golden-piracy: Most crit_success (40.9%), only run with world_state TTL expiry expected (T28, T30)
- zombie-survival: Most condition changes (11), most condition-related issues (lowercase IDs, TTL bug most visible)
- allied-ww2: Most rolls (25), most diverse roll outcomes (includes setbacks)

---

## 5. Root Causes

### condition_ttl bug
**File:** `ccya/engine/turn_state.py:443`
**Cause:** `_expire_conditions()` iterates over `state.pc.conditions` which are `Condition` model objects. The check `if not isinstance(c, dict): continue` skips all model objects, making the TTL decrement logic dead code. The function then calls `state.expire_conditions(expired_ids)` which operates on model objects, but `expired_ids` is always empty because no conditions were processed in the dict loop.

### location_description_consistency masking
**File:** `ccya/ev/checkers/state.py:47`
**Cause:** The checker uses AND logic (`words < min AND sentences < min`) to fail. Since all descriptions have at least 1 sentence, they pass even when severely under the word minimum. This is a design choice that masks short descriptions.

---

## 6. Recommendations

### P0: Fix condition_ttl — **Small effort**
**File:** `ccya/engine/turn_state.py:442-468`
**Change:** Replace the dict-iteration logic with model-object iteration. The function already calls `state.expire_conditions(expired_ids)` which handles `Condition` objects correctly — the dict loop is redundant and buggy. Either:
- (a) Remove the dict loop entirely and rely on `state.expire_conditions()`, or
- (b) Change `if not isinstance(c, dict)` to iterate over model objects and access `.turns_remaining` as an attribute.

**Justification:** The `state.expire_conditions()` method at `state.py:242-263` already correctly decrements TTL on `Condition` model objects. The dict loop in `_expire_conditions()` is dead code that prevents TTL from ever decrementing.

### P1: Tighten location_description_consistency — **Small effort**
**File:** `ccya/ev/checkers/state.py:47`
**Change:** Switch from AND logic to OR logic (fail if words < min OR sentences < min), or raise the minimum sentence threshold to 2.

**Justification:** All 125 examined location descriptions across 5 runs are under 30 words. The checker passes but the descriptions are clearly too short. The checker should flag this.

### P2: Investigate world_state fact additions — **Trivial**
World state facts are static seed data with occasional additions. No issues found, but the dynamic additions (e.g., "The leather dispatch case is in Grant Owens' possession") should be verified to have proper `expires_turn` values. Currently all dynamic facts have `expires_turn=null`.

---

## 7. Meta Improvements

### CHECKERS.md documentation update — **Trivial**
CHECKERS.md line 45 says location_change checker "Only checks turns where `applied.location_change` is present" — this is correct but the doc should clarify that location_change is now emitted by the **State extractor** (not Scene extractor as the old architecture docs imply). The cross-module-contracts.md and step2b-state.md docs are correct; CHECKERS.md may need updating to reflect that location_change is in the State pipeline now.

### ev.py search command limitation — **Minor**
The `ev.py search "applied.location_change:"` command returned no matches because the search syntax doesn't handle nested JSON fields well. The `ev.py turn <N>` or `ev.py deltas <N>` commands are more reliable for inspecting specific turn data.

### condition_ttl checker missing — **Medium effort**
There is no dedicated `condition_ttl` checker in the checker registry. The `world_state_ttl` checker exists but only covers world state facts. A `condition_ttl` checker would verify:
- TTL decrements each turn
- Conditions expire when TTL reaches 0
- Permanent conditions never expire

This would have caught the bug immediately. Adding such a checker would be valuable.

### space-western:explorer run missing
The PHASE-3.md lists 6 runs including `space-western:explorer (25t)`, but only 5 run directories exist on disk. This run may have been deleted or failed to complete. If it exists elsewhere, it should be included in future reviews.

---

## 8. Deep Dive Findings (Post-Review Investigation)

### 8.1 condition_ttl — Confirmed universal across all 5 runs
**Finding:** TTL never decrements on any run. Traced condition lifecycles via `ev.py active-conditions`:
- **zombie-survival:** `exhausted` persists T13-T22 (10 turns), `rattled` persists T14-T25 (12 turns)
- **noir-1930s:** `bruised_ribs` persists T16-T25 (10 turns), `focused` persists T13-T25 (13 turns)
- **space-western:** `burned` persists T22-T25 (4 turns), `rattled` persists T19-T25 (7 turns)
- **allied-ww2:** `concerned` persists T2-T25 (24 turns!)
- **golden-piracy:** `exhausted` persists T5-T11 (7 turns), `rattled` persists T7-T25 (19 turns)

This confirms the `turn_state.py:443` dead code bug is universal — no run shows TTL decrementing.

### 8.2 world_state_ttl — Expiry mechanism never exercised
**Finding:** No run went past any `expires_turn` value. golden-piracy has facts with T28/T30, runs only go to T25. The `expire_world_state_facts()` method was never triggered. This is untested ground — the mechanism may work or may have its own bugs.

### 8.3 location_change — Thread purging NOT implemented (confirmed bug)
**Finding:** cross-module-contracts.md line 15 documents "Scene-scoped threads purged on location change" but the feature is NOT implemented:
1. `ArcThread` model (`state.py:271`) has NO `scope` field
2. `apply_delta()` in `delta_builder.py:216-241` does NOT purge any threads on location change
3. All runs show 0 threads in `pc.arcs.threads[]` — threads live in `long_term_objective.threads[]` instead, which also has no scope field

**Impact:** Threads accumulate permanently across location changes. The documented contract between scene extraction and state management is broken.

### 8.4 location_description_consistency — Consistent within visits, near-miss across similar locations
**Finding:** Descriptions are identical within a single visit to the same location (verified space-western `docking_bay_4` T5-T10 — identical 80-char descriptions). However, noir-1930s has a near-miss:
- `rusty_anchor_tavern` (T1-3): "A rowdy, dim tavern smelling of gin and sawdust, located near the city docks."
- `rusty_anchor` (T20-21): "A dim, smoke-filled tavern smelling of stale beer and cheap tobacco."

Same place (both are taverns near docks), different IDs, different descriptions. The LLM treated them as different locations. This is a prompt/model issue, not a code bug.

### 8.5 conditions_lifecycle — Max concurrent limit exceeded
**Finding:** `ev.py active-conditions` shows max concurrent conditions per run:
- **zombie-survival:** 3 (under limit)
- **noir-1930s:** 4 (under limit)
- **space-western:** 5 (at limit)
- **allied-ww2:** 1 (under limit)
- **golden-piracy:** **7 (EXCEEDS limit of 5)**

golden-piracy T16-T17 has 7 concurrent conditions: bleeding, bleeding_severely, concussed, exhausted, rattled, unconscious, determined. The 5-condition limit is NOT enforced by code — it's a soft cap that the LLM ignores.

### 8.6 inventory_integrity — Lifecycles clean across all runs
**Finding:** Traced full inventory lifecycles for golden-piracy and allied-ww2:
- **golden-piracy:** flintlock_pistol added T1, removed T18. pistol_rounds stays at 6 (never consumed). driftwood_club added T19. All changes match ev.py state-history output.
- **allied-ww2:** intelligence_documents added T1, removed T3. combat_wrench added T1, removed T8. garand_ammo decrements: 40→37 (T11), 37→36 (T19), 36→32 (T22), 32→29 (T23), 29→28 (T24). medical_kit: 2→1 (T18). dispatch_case: added T18, 1→2 (T21). All clean.
- **noir-1930s:** folded_newspaper added T2, persists T25. dollars: 50→45 (T21). All clean.

No negative amounts, no overdraw, no phantom items. Inventory system is working correctly.
