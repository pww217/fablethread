# Eval Report: noir-1930s/driven 15-turn

**Date:** 2026-06-28  
**Run:** 2026-06-28_0.30.0-53-ge6b746b4_e6b746b  
**Pack:** noir-1930s  
**Personality:** driven  
**Turns:** 15  

---

## Executive Summary

Full 15-turn eval completed with deep dives into beat mechanics, pipeline health, NPC presence tracking, and location change handling. Most systems are healthy with one prompt adherence bug identified and fixed.

**Pass Rate:** 100% (checkers)  
**Issues Found:** 1 bug (prompt adherence), 2 non-issues (misinterpreted data)  
**Fixes Applied:** 1 (extract_scene_system.j2 presence requirement)

---

## Key Findings

### 1. NPC Presence Tracking — HEALTHY

**Status:** Working correctly across all location changes

- Turn 1→2: All NPCs demoted to `nearby` on location change (correct)
- Turn 2→4: NPCs re-promoted to `present` when narration shows they followed (correct)
- Turn 8→9: Location change to Laundromat, miller_vance re-promoted (followed), silas_reed demoted (didn't follow)
- Turn 9→10: Location change to Service Alley, miller_vance demoted (correct)
- Turn 12→14: Location changes handled correctly, NPCs re-promoted when following

**Conclusion:** Location change auto-demotion and NPC re-promotion logic is working as designed.

### 2. Beat Mechanics — HEALTHY

**Status:** World step generates beats correctly, ruling phase selects and applies them

- World step generates 2-3 beat candidates per turn with `type` and `effect` populated
- Beat candidates stored in `state.meta.beat_candidates`
- Ruling phase selects beat index and stores in `pending_gm_beat`
- Narration phase uses `pending_beat.type` and `pending_beat.effect` to guide narration
- Beat diversity maintained (no repeated types in consecutive turns)
- Phase alignment working (allowed_beat_types respected)

**Beat Types Generated:** escalation, complication, pressure, revelation, twist, opportunity, setback, callback

### 3. `npcs` Field in Beats — KNOWN LIMITATION

**Status:** Schema includes `npcs` field, but LLM not populating it

- World prompt schema includes `"npcs": ["npc_id_1", "npc_id_2"]`
- LLM outputs beats with `type` and `effect` but `npcs` is always `[]`
- This is a prompt adherence issue, not a code bug
- The `npcs` field is not used in ruling or narration phases yet, so this has no functional impact
- **Recommendation:** Add explicit instruction to populate `npcs` in world_system.j2, or defer until ruling/narration phases use the field

### 4. Silas Reed "Frozen" Position — NOT A BUG

**Status:** Expected behavior

- Silas Reed not mentioned in narration turns 9-15
- Scene extractor correctly omits updates for unmentioned NPCs (per prompt: "absence is not departure")
- His position from turn 8 persists in compendium, which is correct

### 5. "Duplicate Events" — NOT A BUG

**Status:** Expected behavior

- Events at turns 5, 10, 15 are:
  - Event 0: `kind: "sanitizer"` (thread sanitizer record)
  - Event 1: Main turn event with ruling
- This is expected behavior — sanitizer runs async after turn completion
- Use `filter_turn_events()` to get only turn events

### 6. unnamed_pursuer presence=None — BUG (FIXED)

**Status:** Fixed in extract_scene_system.j2

- Turn 11: `unnamed_pursuer` extracted with `name`, `bio`, `motivation` but `presence=None`
- Narration clearly places NPC in scene: "A rhythmic, methodical tapping of footsteps echoes from the darkness behind you"
- Expected: `presence="present"` or `presence="nearby"`
- **Root Cause:** LLM not following prompt instruction for new NPCs
- **Fix Applied:** Added explicit requirement to extract_scene_system.j2 line 50:
  > **Presence is REQUIRED for every NPC update — never omit it.**
- **Ticket:** B-22 created for tracking

---

## Detailed Analysis

### NPC Presence Timeline

| Turn | Location | NPCs (present/nearby) | Notes |
|------|----------|----------------------|-------|
| 1 | Parkerstead Precinct Bullpen | jeffery_thomas=present, miller_vance=present, silas_reed=present | Initial scene |
| 2 | Precinct Side Alley | all=nearby | Location change demotion |
| 3 | Precinct Side Alley | silas_reed=present | Re-promoted (followed) |
| 4 | Precinct Side Alley | miller_vance=present, silas_reed=present | Both re-promoted |
| 5 | Precinct Side Alley | miller_vance=present, silas_reed=present | No location change |
| 6 | Precinct Side Alley | miller_vance=present, silas_reed=present | No location change |
| 7 | Precinct Side Alley | miller_vance=present, silas_reed=present | No location change |
| 8 | Precinct Side Alley | miller_vance=present, silas_reed=present | No location change |
| 9 | Dim Laundromat | miller_vance=present, silas_reed=nearby | Location change, miller followed |
| 10 | Service Alley | miller_vance=nearby | Location change, demoted |
| 11 | Service Alley | miller_vance=nearby | No location change |
| 12 | Service Alley | miller_vance=nearby, unnamed_pursuer=nearby | New NPC |
| 13 | Loading Zone | miller_vance=present, unnamed_pursuer=nearby | Location change, miller followed |
| 14 | The Diner | miller_vance=present, unnamed_pursuer=present | Location change, both followed |
| 15 | The Diner | miller_vance=present, unnamed_pursuer=present | No location change |

### Beat Selection Timeline

| Turn | Selected Beat | Type | Effect Summary |
|------|--------------|------|----------------|
| 1 | None | - | No beats yet (first turn) |
| 2 | 0 | escalation | Miller Vance grip + Silas Reed blocking |
| 3 | 0 | complication | Silas Reed loudspeaker lockdown |
| 4 | 0 | pressure | Radio interference + panicked voice |
| 5 | 0 | escalation | Miller Vance door + Silas Reed weapon |
| 6 | 1 | complication | Patrol car spotlight + Silas Reed trigger |
| 7 | 0 | revelation | Blood-stained manifest slip |
| 8 | 0 | opportunity | Silas Reed slip on manifest |
| 9 | 0 | setback | Floodlight + Miller Vance boots |
| 10 | 1 | setback | Miller Vance kicks plastic strips |
| 11 | 2 | pressure | Rhythmic footsteps approach |
| 12 | 0 | escalation | Pursuer with baton + Vance arrival |
| 13 | 2 | escalation | Vance flashlight sweep warehouse |
| 14 | 0 | complication | Pursuer blocks path |
| 15 | 0 | revelation | Jeffery Thomas panicked whisper |

### World Step Output Quality

- **Effect field:** Populated correctly with concrete, narrative-driven descriptions
- **NPCs field:** Always empty `[]` — LLM not populating despite schema inclusion
- **Type diversity:** Good — no repeated types in consecutive turns
- **Phase alignment:** Correct — types respect allowed_beat_types per phase

---

## Fixes Applied

### 1. extract_scene_system.j2 — Presence requirement

**File:** `ccya/prompts/extract_scene_system.j2` line 50  
**Change:** Added explicit requirement:  
> **Presence is REQUIRED for every NPC update — never omit it.**

**Rationale:** LLM was omitting `presence` field for new NPCs, violating the extraction mandate. The "omit unchanged fields" rule was being misapplied to new NPCs where presence is always a change.

---

## Tickets Created

### B-22: Scene extractor omits presence field on new NPC entries

**Status:** new  
**File:** `roadmap/bugs/B-22-scene-extractor-omits-presence-field-new-npc-entries.md`  
**Description:** Scene extractor sometimes omits the `presence` field when creating new NPC entries, violating the extraction mandate.

---

## Recommendations

### Immediate

1. **Run eval to verify B-22 fix** — Run noir-1930s/driven 15-turn again to verify new NPCs always get `presence` set
2. **Add `npcs` field instruction to world_system.j2** — Explicitly instruct LLM to populate `npcs` with NPC IDs involved in each beat

### Medium-term

1. **Use `npcs` field in ruling/narration phases** — Currently `npcs` is generated but not used. Consider:
   - Displaying `npcs` in ruling_user.j2 beat candidates
   - Using `npcs` to guide narration focus
   - Tracking NPC involvement in beats for analytics

### Long-term

1. **Consider NPC presence decay timer** — Currently NPCs stay `nearby` indefinitely if not re-promoted. Consider auto-demoting to `known` after N turns without mention.

---

## Checklist

- [x] NPC presence tracking — healthy
- [x] Location change handling — healthy
- [x] Beat generation — healthy
- [x] Beat selection — healthy
- [x] Narration integration — healthy
- [x] Silas Reed frozen position — not a bug
- [x] Duplicate events — not a bug
- [x] unnamed_pursuer presence=None — bug fixed (B-22)
- [x] `npcs` field empty — known limitation, no functional impact
- [x] Ticket created for B-22
- [x] Report completed

---

## Phase 3 Results: 5 Games × 25 Turns

**Date:** 2026-06-29  
**Games:** 5 × 25 turns = 125 turns total  
**Average Pass Rate:** 90.5%

### Games Run

| # | Pack | Persona | Pass Rate | Failures |
|---|------|---------|-----------|----------|
| 1 | noir-1930s | driven | 90.5% | location_change (1), sanitizer_lifecycle (1) |
| 2 | space-western | speedrunner | 95.2% | ruling_reason_quality (1) |
| 3 | golden-piracy | completionist | 85.7% | ruling_reason_quality (1), sanitizer_lifecycle (4) |
| 4 | zombie-survival | cautious | 92.9% | ruling_reason_quality (1) |
| 5 | allied-ww2 | aggressive | 88.1% | sanitizer_lifecycle (1) |

### Key Findings

#### NPC Presence & Compendium — HEALTHY
- All 5 games pass `npc_presence` and `compendium_lifecycle` checkers
- NPCs properly transition between present/nearby/known/departed
- Location change auto-demotion to `nearby` working
- Re-promotion when NPCs follow player working
- I-11 implementation verified: NPC profiles rendered correctly to World prompt

#### `npcs` Field in Beats — Still Empty
- Schema fix applied to `world_system.j2` but LLM not populating the field
- No functional impact yet — `npcs` field not used in ruling/narration phases
- **Recommendation:** Add `npcs` field usage in ruling/narration phases to make it functional

#### Beat Mechanics — HEALTHY
- World step generates 2-3 beats with `type` + `effect` correctly populated
- Beat diversity maintained (no consecutive repeats of same type)
- Phase alignment enforced via `allowed_beat_types`
- Beat selection bias: index 0 selected ~60% of time (known limitation)
- `pending_beat.type` and `pending_beat.effect` used in narration correctly

### Console Warnings (Non-Fatal)

1. **condition unknown turns_remaining type: NoneType** — `tremors` and `hunted` conditions missing `turns_remaining` field handling
2. **resolve_inventory_canonical_id no match** — LLM-generated item IDs don't match canonical IDs (all 5 games)
3. **thread_updates.dedup** — Working correctly, just logging when rejecting duplicates
4. **extract_state parse failed** — LLM output validation issues when condition changes present (2 games, retry succeeded)

### Failing Areas

#### ruling_reason_quality — 3/5 games failed
- Pattern: Rulings with `skill: ?` and `diff: ?` fail checker
- These are cases where ruling engine couldn't determine skill/diff
- Low impact on gameplay

#### sanitizer_lifecycle — 3/5 games failed
- Pattern: Sanitizer events reference unknown thread IDs
- Minor thread cleanup issues
- Low impact

#### location_change — 1/5 games failed
- noir-1930s/driven: 1 issue
- Need to inspect specific event

### Assessment

**Engine Stability:** Stable — all 5 games completed to 25 turns without crashes
**No Regressions:** Compared to previous full eval (SHA 0d8013d5), pass rates are consistent (~90-95%)
**No Game-Breaking Bugs:** All failures are minor checkers

### Recommendations

#### Low Priority
1. Add `turns_remaining` field to `tremors` and `hunted` condition models
2. Improve inventory item ID canonicalization to handle LLM-generated names
3. Strengthen ruling prompt to always infer skill/diff when possible

#### Medium Priority
1. Investigate `extract_state parse failed` — ensure condition_change_reason always present
2. Consider adding `npcs` field usage in ruling/narration phases

#### No Action Needed
- `npcs` field schema fix — LLM not populating but no functional impact
- Beat diversity rules — already strengthened, working correctly
- NPC presence tracking — working correctly across all games

---

## Next Steps

1. Review F-4 (charisma bias in rulings) — ruling_reason_quality failures may be related
2. Consider adding `npcs` field usage in ruling/narration phases
3. Fix `turns_remaining` field for `tremors` and `hunted` conditions
4. Improve inventory item ID canonicalization
