---
title: "Convergence-proactive plan: 3-run eval findings (noir, allied, zombie)"
status: done
created: 2026-06-27
ticket_id: E-1
labels:
  - eval
  - engine
  - pacing
  - extraction
  - prompt
---

## Context

Eval group `2026-06-27_0.30.0-28-g0d8013d5_0d8013d` — 3 runs, 15 turns each:
- noir-1930s / driven (15 turns)
- allied-ww2 / aggressive (15 turns)
- zombie-survival / cautious (15 turns)

Prior SHA: `8ec9d3b` (branch: `convergence-proactive-plan`). One massive commit touched 37 files: beat pipeline simplification, 6-component convergence, signal-gated CLIMAX exit, phase machine moved pre-ruling, index-based beat selection, static pack removal, prompt fixes.

Checker scores: Noir 23/25 (92%), Allied 39/42 (92.9%), Zombie 24/25 (96%).

---

## Finding 1: `config` NameError in `_compute_pacing_context:221` — CLIMAX hard cap broken

**Severity:** High
**Root cause:** `ccya/engine/_pacing.py:221` references `config.climax_turn_limit` but `config` is never defined in the function scope or at module level. The caller (`narrate.py`) defines `config = ctx.config` locally, but `_compute_pacing_context` doesn't receive it as a parameter.

**Evidence:**
- Noir T8: `climax_turn_count=4 >= limit` but `outcome_hint='advance'` (should be `'transition'`)
- Zombie T7: `climax_turn_count=4 >= limit` but `outcome_hint='hold'` (should be `'transition'`)

**Impact:** The CLIMAX hard-cap override that forces `outcome_hint='transition'` when `climax_turn_count >= limit` is completely broken. The LLM's `scene_motion`/`outcome_hint` can override the engine's hard cap, allowing CLIMAX to stretch beyond intended duration.

**Fix:** Pass `config` as a parameter to `_compute_pacing_context`, or use a default limit constant.

---

## Finding 2: Phase transitions firing without required triggers

**Severity:** Medium
**Root cause:** The LLM's `scene_motion: advance` from the ruling step is being treated as an equivalent trigger for phase transitions, bypassing the engine's required thresholds.

**Evidence:**
- Noir T3: SETUP→RISING without urgent thread, `turns_in_phase=0`
- Noir T13: BREATHER→RISING without urgent thread, `breather_turn_count=0`

The checker `phase_transition_signals` flags these because the output phase changed without the required engine triggers (urgent thread or turn-count threshold).

**Impact:** The convergence-proactive plan was meant to make the engine more proactive, but the LLM's `scene_motion: advance` is being used as an additional signal that can override the engine's conservative thresholds, defeating the purpose of the convergence score.

**Fix:** Either enforce that `scene_motion: advance` alone cannot trigger a phase transition, or document that the engine's required triggers are soft constraints that can be overridden by the LLM.

---

## Finding 3: RISING→CLIMAX at score 2, below threshold of 3

**Severity:** Medium
**Root cause:** Same as Finding 2 — the LLM's `scene_motion: advance` is overriding the convergence threshold check in `_compute_scene_phase`.

**Evidence:**
- Noir T5: Score=2, threshold=3, transition still happened
  - `urgent_thread: 0`, `threat_thread: 0`, `scene_age: 1`, `beat_streak: 0`, `roll_starvation: 0`, `threat_density: 0`, `stall_floor: 1`
  - Total: 2 (scene_age + stall_floor)
  - All threads were `normal`/`background` urgency, no threat-type threads

The threshold was raised from 2→3 in the commit, but the transition still fired because the LLM's `scene_motion: advance` was used as an equivalent trigger.

**Impact:** Premature CLIMAX entries, compressed pacing. The convergence score threshold is effectively meaningless if the LLM can override it.

**Fix:** Same as Finding 2 — enforce that convergence threshold is a hard gate, not a soft suggestion.

---

## Finding 4: State extraction retries — `condition_change_reason` missing ✅ VALIDATED

**Severity:** Medium
**Root cause:** The state extractor prompt (`extract_state_system.j2`) needs to enforce `condition_change_reason` as required when conditions are added/changed. The model is adding `pc_condition_add` entries without providing the reason.

**Evidence:**
- Allied T13: `EXTRACTION_COERCION_FAILED: condition_change_reason is required when condition changes are present` (1 retry, ~24.7s)
- Allied T15: Same error (1 retry, ~21.2s)
- Retry succeeded on both (final `applied` field shows `condition_change_reason: "PC moved into a fast-moving creek and ravine"` on T13)

**Impact:** 2 retries = ~46 seconds of extra latency, potential state loss on retry failure.

**Fix:** Strengthen the state extractor prompt to require `condition_change_reason` when `pc_condition_add` or `pc_condition_remove` is present.

---

## Finding 5: High thread dedup rate in allied run ✅ VALIDATED

**Severity:** Low
**Root cause:** Either the thread naming is too broad (e.g., "enemy_encroachment" covers too much ground), or the LLM needs stronger guidance on when to create new progress entries vs. when to skip.

**Evidence:**
- 7 total rejections in allied run (vs. 2 in noir, 2 in zombie)
- `enemy_encroachment`: 3 rejections (T2, T3, T4) — nearly identical "machine-gun fire" progress entries (0.71–0.77 similarity)
- `supply_diversion_route`: 2 rejections (T12 at 1.0 similarity, T15 at 0.71)
- `internal_hostility`: 1 rejection (T6, 0.92 similarity)
- `mysterious_stranger`: 1 rejection (T10, 0.83 similarity)
- T12 had **1.0 similarity** — identical progress entry

**Impact:** Thread fragmentation, redundant progress entries, reduced signal-to-noise in thread state.

**Fix:** Either tighten thread naming in the world step prompt, or strengthen the dedup guidance in the state extractor.

---

## Finding 6: Inventory canonical ID on first add ✅ VALIDATED ✅ FIXED

**Severity:** Low
**Root cause:** When items are first added to the inventory, `resolve_inventory_canonical_id()` returns `None` because the item doesn't exist yet in the inventory to match against. The item gets added with `item.id` as the target, but the extraction event lacked a `canonical_id` field on first add.

**Evidence:**
- Noir: `case_dismissal_files` (T1), `arrest_files` (T2), `leather_bound_ledger` (T3), `revolver_rounds` (T5)
- Allied: `family_letters` (T2), `service_pistol` (T4, T5), `redacted_parchment` (T9), `leather_satchel` (T14, T15), `small_arms_ammo` (T14, T15), `pistol_rounds` (T16)
- Zombie: `data_slate` (T2), `medical_canister` (T7, T10), `militia_manifest` (T12)

**Verified:** All items DO exist in final `state.yaml` with correct canonical IDs (e.g., `case_dismissal_files` has `id=case_dismissal_files, name=Case Dismissal Files`). The issue is purely that the first extraction event lacked a `canonical_id` field — subsequent additions match correctly.

**Fix Applied:**
1. Pass pack inventory through `TurnContext.packing` → `_extract_state_messages()` → Jinja template
2. Updated `extract_state_system.j2` schema to include `canonical_id` in `inventory_add` items
3. Added pack inventory reference section so LLM can match new items against known pack definitions
4. Updated prompt instructions to require `canonical_id` for all `inventory_add` items

---

## B-10 (testing) — Fixes present, needs validation

All three fixes from B-10 are in the current codebase:

1. **Jinja2 JSON bug** ✅ — `ccya/templates/index.html:500`: `{{ (state if state else {}) | tojson | safe }}`
2. **Numeric words exemption** ✅ — `ccya/static/game-utils.js:507`: `numericWords` Set with one-through-ten
3. **NPC naming prompt** ✅ — `ccya/prompts/narrate_system.j2:80`: strengthened NPC NAMING rule

Item 3 (non-roll tooltip) is marked as a separate, unrelated issue — not fixed.

**Recommendation:** B-10 should remain in `testing` until a live game validates the highlighting works end-to-end.

---

## Recommendations

1. **Fix `config` NameError in `_compute_pacing_context`** ✅ FIXED
2. **Enforce convergence threshold as hard gate** ✅ FIXED
3. **Strengthen state extractor prompt for `condition_change_reason`** ✅ FIXED
4. **Review thread naming in world step** — allied run has 3.5x the dedup rate of other runs (7 vs 2)
5. **Pass pack canonical IDs to extraction pipeline** ✅ FIXED
6. **Validate B-10 fixes with live game** — code is present, UI behavior unconfirmed
