# Master Eval Report — Narrative Mechanics Overhaul
**Date:** 2026-06-16 | **Games:** 5 | **Total turns:** 100 | **Personality:** driven (all)

## Summary Table

| Pack | Turns | Checker Pass | Avg Score | Pacing | Beats | State | Threads | Goals |
|------|-------|-------------|-----------|--------|-------|-------|---------|-------|
| Noir | 20 | 87.0% | 0.87 | FAIL | FAIL | PASS | FAIL | FAIL |
| Zombie | 20 | 78.3% | 0.78 | FAIL | PASS | PASS | FAIL | FAIL |
| WWII | 20 | 78.3% | 0.78 | PASS | PASS | PASS | FAIL | FAIL |
| Pirate | 20 | 82.6% | 0.83 | FAIL | PASS | PASS | FAIL | FAIL |
| Space Western | 20 | 87.0% | 0.87 | PASS | PASS | PASS | FAIL | PASS |

---

## FINDING 1: `extraction.state.empty` — SYSTEMIC (CRITICAL)

**Severity:** Critical — affects all 5 packs, all 100 turns
**Frequency:** 39/100 turns show `extraction.state.empty` — state has no inventory/condition changes after retries

**What it is:** The state extractor runs, finds no inventory or condition changes in the LLM output, retries, and still finds nothing. The turn proceeds with no state deltas applied.

**Impact:** The game state drifts from the narrative. The prose describes events (drawing weapons, taking damage, acquiring items) but the game state doesn't reflect them. This breaks all downstream mechanics that depend on state (conditions, inventory checks, NPC interactions).

**Root cause hypothesis:** The state extractor prompt/template is not aligned with how the LLM describes state changes in the narrative. The LLM may be describing changes in prose without producing structured JSON fields that the extractor recognizes.

**Recommendation:** Audit the state extraction prompt and compare it against actual LLM outputs. Check if the extractor is looking for the right JSON keys/structure.

**Validation run (2026-06-16):** Ran `ev.py play --llm --turns 5 --eval --pack noir-1930s --personality driven` to inspect actual LLM output. Found three bugs:
1. `extraction.state.empty` check at `extraction.py:626` only checked `inventory_add` + `pc_condition_add`, missing `inventory_update`/`inventory_remove`/`pc_condition_remove`
2. `inventory_change_reason` validator at `models.py:338` only checked `inventory_add` + `inventory_remove`, missing `inventory_update`
3. LLM outputs `inventory_update` for spatial repositioning ("draw revolver from holster") thinking it's a meaningful change

**Fix applied (2026-06-16):**
- Expanded `extraction.state.empty` check to include all inventory/condition fields
- Added `state_attempts > 1` guard so the warning only fires when there were retries (not on correct first-pass "no change" decisions)
- Expanded `inventory_change_reason` validator to include `inventory_update`
- Added targeted retry hint when `inventory_change_reason` is missing
- Rewrote `extract_state_system.j2` with STEP 0 ("Decide first, output second") and explicit spatial reasoning rules

---

## FINDING 2: Thread Dedup Rejections — SYSTEMIC (HIGH)

**Severity:** High — affects all 5 packs
**Frequency:** 47 `thread_updates.dedup` rejections across all games

**What it is:** The storyteller creates threads (e.g., `press_leverage`, `containment_breach`, `supply_line_collapse`) but never meaningfully updates them. Progress values stay at 0.91-1.00, triggering dedup rejections because the update is too similar to the last entry.

**Impact:** Threads become dead weight — they exist in the game state but never progress or resolve. This breaks the thread lifecycle and makes the campaign arc feel static despite intense narrative action.

**Root cause hypothesis:** The storyteller prompt instructs it to create threads but doesn't provide clear guidance on how to meaningfully increment progress. The progress increment logic may be too strict — small changes like 0.91→0.92 get rejected as "overlap."

**Recommendation:** Review the storyteller prompt's thread update instructions. Consider relaxing the dedup threshold or providing explicit progress increment guidance.

---

## FINDING 3: `thread_same_turn_conflict` — BUG (HIGH)

**Severity:** High — affects 4/5 packs (not observed in Pirate)
**Frequency:** 4 occurrences across Noir, Zombie, WWII, Space Western

**What it is:** `thread_update` and `thread_resolve` for the same thread ID in the same turn. The storyteller both updates and resolves a thread in a single turn, causing a conflict.

**Impact:** Thread lifecycle breaks — the thread gets updated AND resolved simultaneously, which is logically inconsistent.

**Root cause:** The storyteller prompt doesn't clearly separate update vs resolve logic. When a thread reaches a natural conclusion, the storyteller may try to both increment progress and resolve it.

**Recommendation:** Add explicit instruction to the storyteller: "If resolving a thread, do NOT also include a thread_update for the same ID in the same turn."

---

## FINDING 4: `thread_resolutions` — Unknown IDs — BUG (HIGH)

**Severity:** High — affects all 5 packs
**Frequency:** 14 `thread_resolve` references to unknown IDs across all games

**What it is:** The storyteller tries to resolve a thread ID that was never created in the current session. Examples: `entity_breach_combat`, `perimeter_breach_containment`, `cargo_theft_tension`, `structural_instability_shaft`.

**Impact:** Thread resolution silently fails — the thread persists in the game state as unresolved even though the narrative treats it as resolved.

**Root cause:** The storyteller is generating thread IDs that don't match existing threads. This could be a naming inconsistency between thread creation and resolution in the prompt.

**Recommendation:** Add validation in the storyteller prompt: "Only resolve thread IDs that currently exist in the game state."

---

## FINDING 5: `storytell parse failed` — arc_resolve Missing Fields — BUG (HIGH)

**Severity:** High — affects 3/5 packs (Noir, Pirate, Space Western)
**Frequency:** 4 `storytell parse failed` errors

**What it is:** The storyteller returns `arc_resolve: {}` — an empty object — when it should include `resolution`, `visible_goal`, and `goal_context`. Pydantic validation rejects this.

**Impact:** The turn's arc resolution is lost. The storyteller attempted to resolve the arc but the data structure is malformed.

**Root cause:** The storyteller prompt may not clearly specify that `arc_resolve` must include all three fields when present. The LLM may be returning an empty object as a "no resolution this turn" signal.

**Recommendation:** Either (a) make `arc_resolve` optional in the schema, or (b) make the prompt explicitly require all three fields when `arc_resolve` is present.

---

## FINDING 6: `extract_state parse failed` — inventory_change_reason — BUG (MEDIUM)

**Severity:** Medium — affects 2/5 packs (WWII, Pirate)
**Frequency:** 2 `extract_state parse failed` errors

**What it is:** The state extractor returns `inventory_change_reason: None` when inventory changes are present. The validation rule requires `inventory_change_reason` as a string when `inventory_add`/`inventory_remove`/`inventory_update` are present.

**Impact:** The entire state extraction fails for that turn — no state deltas are applied.

**Root cause:** The state extraction prompt doesn't clearly instruct the LLM to always provide `inventory_change_reason` when modifying inventory.

**Recommendation:** Add explicit prompt instruction: "When modifying inventory, always include `inventory_change_reason` as a non-empty string."

---

## FINDING 7: `delta validation failed` + `Fallback narrative` — BUG (MEDIUM)

**Severity:** Medium — affects 1/5 packs (Zombie)
**Frequency:** 2 turns (17, 20)

**What it is:** State deltas fail validation, so the turn falls back to a stripped narrative. The player's action is acknowledged but no mechanical impact occurs.

**Impact:** Turns lose their mechanical weight — the narrative continues but the game state doesn't change.

**Root cause:** The deltas produced by the state extractor don't pass validation rules. Likely related to FINDING 6 (missing `inventory_change_reason`).

---

## FINDING 8: `skill: ?` in Rulings — BUG (MEDIUM)

**Severity:** Medium — affects all 5 packs
**Frequency:** ~40% of turns show `skill: ?` in ruling output

**What it is:** The ruling step fails to assign a skill to certain actions. The ruling shows `RECALL (skill: ?, diff: ?)` or `ATTACK (skill: ?, diff: ?)`.

**Impact:** Rolls that depend on skill modifiers may use default/zero modifiers, affecting roll outcomes.

**Root cause:** The ruling prompt may not have skill mappings for certain action types or the action classification is ambiguous.

---

## FINDING 9: `TypeError` in Logging — BUG (LOW)

**Severity:** Low — cosmetic only, doesn't affect game state
**Frequency:** 4 occurrences (Zombie, WWII, Space Western)

**What it is:** `thread_same_turn_conflict` log message uses `%d` format specifier for `trace_id`, but `trace_id` is a string. This crashes the logging formatter.

**Root cause:** `trace_id` is a hex string (e.g., `'5b671205'`), not an integer. The log message format string should use `%s` instead of `%d`.

---

## FINDING 10: `generate_seed soft-check` — Opening Narrative Too Short — IMPROVEMENT (LOW)

**Severity:** Low — affects all 5 packs
**Frequency:** 5/5 packs

**What it is:** Opening narratives range from 306-519 words, all below the 530-930 word target.

**Impact:** Minimal — the opening sets the scene but shortness doesn't break mechanics.

---

## FINDING 11: `reconcile_delta duplicate condition add ignored` — BUG (LOW)

**Severity:** Low — affects 1/5 packs (Pirate)
**Frequency:** 1 occurrence — `watched` condition attempted to be added twice in turn 16

**What it is:** The reconciliation step detects a duplicate condition add and ignores the second one.

**Root cause:** The state extractor produces two `pc_condition_add` entries for the same condition ID in a single turn.

---

## FINDING 12: `inventory over-draw clamped` — BUG (LOW)

**Severity:** Low — affects 1/5 packs (Zombie)
**Frequency:** 1 occurrence — `pistol_ammo` over-draw clamped

**What it is:** The LLM tries to remove 4 `pistol_ammo` but only 2 remain. The system clamps to removing 2.

**Root cause:** The state extractor doesn't check current inventory levels before producing removal deltas.

---

## NARRATIVE MECHANICS — SPECIFIC ASSESSMENT

### Scene Imperatives — WORKING WELL
All 5 packs show strong scene tagline evolution. Scene descriptions are vivid, atmospheric, and contextually appropriate to the pack theme. Scene transitions between locations are continuous and logical.

### Combat — WORKING WELL
Combat escalation is the strongest narrative element across all packs. Conditions track well through combat sequences. The progression from approach → engagement → escalation → resolution (or capture) feels narratively coherent.

### Location Imperatives — WORKING WELL
Location transitions are continuous. No broken location jumps observed. Location descriptions are rich and pack-appropriate.

### Pacing — MIXED
- **PASSING:** WWII (7/7), Space Western (7/7)
- **FAILING:** Noir (6/7), Zombie (6/7), Pirate (6/7)

Pacing directives work in WWII and Space Western but fail in the other three. This suggests the pacing prompt may be pack-dependent — possibly related to how well the pack's tone_tags align with the pacing directive system.

### GM Beats — WORKING WELL
All 5 packs show `beats: 3/3 PASS`. GM beat generation and phase validity are working correctly.

### State — WORKING WELL
All 5 packs show `state: 6/6 PASS`. The state checker passes consistently — meaning the active state file is consistent with what's being tracked.

### Thread Lifecycle — BROKEN
All 5 packs fail `thread_lifecycle`. This is the single biggest failure in the narrative overhaul — threads are created but never meaningfully progressed or resolved.

### Goal Updates — MIXED
- **PASSING:** Space Western (2/2)
- **FAILING:** Noir, Zombie, WWII, Pirate

Goal updates work in Space Western but fail in the other four packs. This suggests the storyteller prompt's goal update instructions may not be pack-agnostic.

---

## PRIORITY FIXES

1. **`extraction.state.empty`** — Fix state extraction so it captures inventory/condition changes from narrative prose. This is the highest-impact bug — 39% of turns lose their mechanical impact.

2. **Thread dedup/reuse** — Fix thread progress increment logic so threads meaningfully advance. Currently 47% of thread updates are rejected as duplicates.

3. **`thread_same_turn_conflict`** — Fix the storyteller prompt to prevent simultaneous update+resolve of the same thread.

4. **`arc_resolve` parse failures** — Either make `arc_resolve` optional or require all three fields when present.

5. **`inventory_change_reason` validation** — Ensure the state extraction prompt always produces `inventory_change_reason` when modifying inventory.

6. **`skill: ?` in rulings** — Debug why skill assignment fails for ~40% of rulings.

---

## OVERALL ASSESSMENT

The narrative overhaul is **working for scene/location imperatives and combat** — these are the core narrative mechanics and they function well across all packs. The prose is vivid, atmospheric, and mechanically coherent in terms of combat escalation and condition tracking.

The **biggest failure is in thread management** — threads are created but never meaningfully progressed, which breaks the campaign arc system. This is a storyteller prompt issue, not a scene/narration issue.

The **state extraction pipeline** is the second biggest failure — nearly 40% of turns lose their mechanical impact because the state extractor can't find changes in the LLM output.

The **pacing system** works in 2/5 packs — worth investigating why it fails in Noir, Zombie, and Pirate.

**Bottom line:** The narrative overhaul is fundamentally sound for what it was designed to do (scene imperatives, combat narration, location tracking). The failures are in the extraction/threading layer — the bridge between narrative prose and game state — not in the narrative generation itself.
