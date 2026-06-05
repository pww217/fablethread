# Eval Findings — Latest Run Summary

**Run:** `2026-06-05T20:24:42Z` · Scenario: `full_cycle` (13 turns)  
**Pack:** `eval-pack` · Model: `mlx-community/gemma-4-26b-a4b-it-mxfp8`  
**State Fidelity Rate:** 0.538 (7/13 clean turns)

---

## Critical Issues

### C1 — Floor Relief Override Failure (turns 8–10) [FIXED]
When `beat_locked=True` and Storytell emitted pressure-type beats (`complication`, `pressure`, or `escalation`), the floor relief mechanism failed to override them with `breathing_room`. The lock was active at momentum=-3 for turns 7–10, but only injected on null/missing storytell output — not when storytell actively emitted a pressure beat.

**Tag:** engine_bug  
**Fix:** Moved injection from post-`apply_delta()` to pre-`apply_delta()`, right after Storyteller's `gm_beat` is written to state (turn.py ~line 1032). The override now persists through the deep copy. Post-apply injection removed as redundant. Plan: `/plans/fix-floor-relief-override-bug.md`.

### C2 — State Fidelity Rate: 53.8% (7/13 clean turns)
Only half the turns passed all assertions without drift, engine bugs, or auto-checker failures. Well below acceptable quality for production.

**Proposed fix:** Address root causes in C1–C4. The floor relief bug alone accounts for failed turns T8/T9 plus contributed to pacing metric failure on T10.

---

## Major Issues

### M1 — Phantom Inventory Removal (ledger, turn 12)
State Extract emitted `inventory_remove[ledger]` but the ledger was never in Aren's inventory. Narrative implied he "grabbed" it, but no prior state_add existed. State corruption risk where items can be removed without being present.

**Tag:** extraction_miss  
**Proposed fix:** In State Extract pipeline, validate item existence before emitting `inventory_remove`. If narrative implies possession without state tracking, emit an `inventory_add` first or flag as extraction error rather than silently removing non-existent items.

### M2 — Extraction Amount Mismatch (credits, turn 6)
Narrative said "drop 200 credits" (failed bribe). Extract removed only 5. Expected: either 0 (bribe failed, nothing taken) or 200 (snatched). LLM hallucinated a small amount instead of honoring stated quantity or interpreting failure correctly.

**Tag:** extraction_miss  
**Proposed fix:** Add validation to State Extract that flags large discrepancies between narrated quantities and extracted amounts. Consider adding explicit "failed" outcome handling in extraction prompts so failed transactions don't produce partial removals.

### M3 — Condition Orphan (`unsteady`, turn 10)
Condition `unsteady` was added to state but had no entry in `CONDITION_MODS`, meaning it provides no mechanical benefit/detriment, breaking game balance consistency.

**Tag:** schema_drift  
**Proposed fix:** Register all valid condition IDs/modifiers in a central engine constant or registry. When State Extract adds a new condition not in the registry, either map to closest known equivalent or register dynamically with default values (e.g., `stat_check_penalty: -1`).

---

## Minor Issues

### N1 — NPC Mention False Positives ("Marrow" T4, "Above" T9)
Auto-checker flagged narration mentions not in compendium. "Marrow" is part of location name (Marrow's Crossing), likely a false positive. "Above" may be implicit NPC reference from narrator prose.

**Tag:** scope_violation  
**Proposed fix:** Scope the NPC mention checker to exclude location names and generic directional nouns. For genuine implicit references, improve narrator grounding prompts or add them to scene context.

### N2 — Beat Type Variety Collapse (turns 6, 9–10)
Beats were >60% `pressure`/`complication`, indicating a narrow beat palette during combat sequence. Expected under high pressure but worth monitoring for repetitive narration.

**Tag:** pacing  
**Proposed fix:** No immediate engine change needed. Consider adding directive-level variety enforcement in Storytell when consecutive beats exceed threshold, or accept as valid behavior under floor conditions.

---

## Auto-Checker Summary

**312 passed, 25 failed** across 13 turns (24 assertions per turn).

### Universal Assert Failures by Severity

| Assertion | Severity | Turns Failed | First Failure |
|-----------|----------|-------------:|---------------|
| `extract.scene.scene_tags` | 🔴 Critical | 2 | T5 |
| `extract.state.inventory_add` | 🔴 Critical | 1 | T11 |
| `extract.state.inventory_remove` | 🔴 Critical | 2 | T6 |
| `extract.state.pc_condition_add` | 🔴 Critical | 1 | T11 |
| `extract.state.pc_condition_remove` | 🔴 Critical | 2 | T12 |
| `ruling.rolled` | 🔴 Critical | 5 | T2 |
| `storytell.extract.thread_resolve` | 🔴 Critical | 1 | T7 |
| `storytell.extract.thread_update` | 🔴 Critical | 2 | T2 |
| `universal.conditions.orphan` | 🔴 Critical | 1 | T10 |
| `universal.inventory.remove_existence` | 🔴 Critical | 1 | T12 |
| `universal.npc_mention.extracted` | 🔴 Critical | 2 | T4 |
| `universal.beat_type.variety` | 🟡 Minor | 3 | T6 |
| `universal.pacing.floor_no_relief` | 🟡 Minor | 2 | T9 |

### Assertion Detail by Turn

**T2:** `ruling.rolled`, `storytell.extract.thread_update[settle_the_debt]`  
**T4:** `universal.npc_mention.extracted` ("Marrow" not in compendium)  
**T5:** `extract.scene.scene_tags[standoff]`, `storytell.extract.thread_update[clear_the_road_toughs]`  
**T6:** `extract.state.inventory_remove[credits]=5`, `universal.beat_type.variety` (67% pressure)  
**T7:** `storytell.extract.thread_resolve[deliver_the_ledger]` not found  
**T8:** `extract.state.inventory_remove[brass_key]` not found  
**T9:** `extract.scene.scene_tags[social]`, `universal.npc_mention.extracted` ("Above"), `universal.pacing.floor_no_relief`, `universal.beat_type.variety` (67% complication)  
**T10:** `ruling.rolled`, `universal.pacing.floor_no_relief`, `universal.conditions.orphan[unsteady]`, `universal.beat_type.variety` (100% complication)  
**T11:** `extract.state.pc_condition_add[winded]`, `extract.state.inventory_add[wax_sealed_cylinder]` not found  
**T12:** `ruling.rolled`, `extract.state.pc_condition_remove[winded]`, `universal.inventory.remove_existence[ledger]`  
**T13:** `extract.state.pc_condition_remove[bruised_ribs]`

---

## Pacing Metrics

### Long Threads (>8 turns)
| Thread | Duration | Flagged |
|--------|----------|---------|
| `clear_the_road_toughs` | 12 turns (T1–T13) | ⚠️ |
| `deliver_the_ledger` | 12 turns (T1–T13) | ⚠️ |

### Location Dwell (>4 turns)
| Location | Turns Active | Flagged |
|----------|-------------:|---------|
| `crossed_keys_entrance` | 8 | ⚠️ |

### Momentum Floor Runs
| Start | End | Duration |
|-------|-----|----------|
| T7 | T10 | 4 turns |

---

## Judge Scores

- **Mechanical:** —/5 (unscored, auto-checker used instead)
- **Narrative:** —/5 (unscored)
- **System Cohesion:** —/5 (unscored)
- **Prompt Quality:** —/5 (unscored)
- **State Fidelity Rate:** 0.538
- **Extraction Accuracy Score:** 2/5
- **Mechanic Lifecycle Score:** 4/5

---

*Generated from: `evals/runs/20260605T202442Z_havr6lvx/REPORT.md`*
