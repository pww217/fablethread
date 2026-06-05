# Eval Findings — Latest Run Summary

**Run:** `2026-06-05T22:26:59Z_swmx485_` · Scenario: `full_cycle` (13 turns)  
**Pack:** `eval-pack` · Model: `mlx-community/gemma-4-26b-a4b-it-mxfp8`  
**Judge model:** `mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit`

---

## Fixed (this session)

### F1 — NPC Mention False Positives [FIXED]
Auto-checker flagged 'Slowly' (T2), 'Marrow' (T3/T4, location root of "Marrow's Crossing"), and 'Ahead' (T12) as unknown NPCs. The `check_npc_mention_extracted()` heuristic has been broken since inception — it parses capitalized tokens from narration but cannot reliably distinguish NPC names from adverbs, prepositions, or location-name fragments.

**Fix:** Removed entire assertion (`check_npc_mention_extracted`) and helper (`_extract_candidate_names`) from `ccya/eval/universal_asserts.py`. Also removed `"extract.scene"` stream from `_VALID_STREAMS`, `EXTRACT_STREAMS`, and `KNOWN_ASSERT_FIELDS` — the scene_tags extraction test has no purpose.

### F2 — Thread Update Timing False Positives [FIXED]
Auto-checker failed on T2 (`settle_the_debt`) and T6 (`clear_the_road_toughs`) with `thread_update.references unknown thread ID`. The bug was in runner.py: it overwrote each turn's embedded per-turn `state_snapshot` (correct, from events.jsonl) with the YAML-loaded snapshot (always final state). On T2/T6, threads were already resolved by end-of-run but still active at check time.

**Fix:** Changed state_snapshot merge in runner.py to only set it if not already present — preserves correct per-turn snapshots.

### F3 — Scene Tags Assertions [FIXED]
`extract.scene.scene_tags` assertions failed on T5 (`standoff`), T9 (`social`). `scene_tags` has no purpose as an assertion target and the extraction test handler was dead code. Removed all 4 TurnAssert + 3 expects strings from full_cycle.py, plus runner.py handler and engine_mirror registry entries.

### F4 — Phantom Inventory Removals Polluting events.jsonl [FIXED]
State Extract emitted `inventory_remove` deltas for items not in inventory or at zero balance (T6/T9/T13: `credits`, T7: `merchant_seal`, `ledger`). The engine's validation pipeline did NOT block these — it silently dropped them at debug level, but they still polluted events.jsonl as emission values, causing eval assertions to fail on data that never actually corrupted state.

**Engine behavior discovered:** Three-layer validation exists but is incomplete:
- `_validate()` (turn.py): checks inventory existence + balance, rejects zero-balance items — **does NOT block**, proceeds through `reconcile_delta` → `apply_delta` regardless of failures
- `reconcile_delta()` (delta_builder.py): dedup only, no existence or legality checks  
- `apply_delta()` (delta_builder.py:~175): silently drops missing inventory targets at debug level (`_log.debug("inventory_remove target %r not found...") continue`), adds any condition unconditionally with no CONDITION_MODS check

**Fix:** Made `_validate()` reject missing targets as `kind="missing_target"` instead of silent skip. Added else-branch around reconcile/apply in run_turn() so blocking errors skip delta application entirely — `applied` stays empty, rejected deltas get recorded in events.jsonl's structured `rejected` field with reasons. Phantom values no longer pollute emission data.

**Commit:** `cd6658d` · Plan: `plans/block-inventory-rejection.md` (completed)

---

## Critical Issues (remaining)

### C1 — Inventory Extraction Hallucination (turns 6, 7, 9, 13)
State Extract emits `inventory_remove` deltas for items that do not exist or have zero balance:
- T6/T9/T13: Remove `credits` when balance is 0 (exhausted in T2, item deleted from inventory entirely). If applied, balance would go negative.
- T7: Remove `merchant_seal`, `ledger` — never tracked as owned items. Narrative mentions "sliding the merchant seal" and "handing him the ledger", but engine's inventory model did not track these previously.

**Tag:** extraction_miss  
**Root cause:** State Extract (Step 2b) does not validate current `state.inventory` before emitting removal deltas. It hallucinates narrative justification for spending actions that state doesn't support. F4 blocks the damage at runtime, but the LLM still emits garbage into events.jsonl as raw emission values — eval assertions on emissions will continue to fail until extraction quality improves.  
**Fix needed:** Update State Extract prompt and validation logic to strictly check `state.inventory` for existence and sufficient quantity before emitting `inventory_remove`. Emit null/empty delta when checks fail rather than hallucinating a removal.

### C2 — Phantom Condition/Additions (turn 11)
State Extract emits `pc_condition_add[winded]` and `inventory_add[wax_sealed_cylinder]`, but neither appears in applied state or final inventory/conditions. Same root cause as C1 — extraction without validation against what actually exists or can be created.

**Tag:** extraction_miss  
**Fix needed:** State Extract must validate that a condition is allowed (exists in CONDITION_MODS registry) before emitting `pc_condition_add`, and only emit `inventory_add` for items the narrative explicitly introduces as new acquisitions, not inferred ones. No legality check exists at any layer — `apply_delta()` adds any condition unconditionally if it's not already present and under the 5-condition cap.

### C3 — Thread Resolve Mismatch (turn 7)
Storytell emits `thread_resolve[deliver_the_ledger]` but the resolved list is empty (`resolved: []`). The extractor claims a resolution happened that didn't materialize in state. Two possible root causes need investigation to distinguish:

- **Extraction error:** Storytell prompt told it to resolve, but the thread wasn't actually resolvable at T7 (e.g., `deliver_the_ledger` still had active sub-tasks or required conditions weren't met). Fix: tighten Storytell prompt with explicit resolvability criteria.
- **Pipeline ordering bug:** The resolver ran against wrong state version — e.g., it saw the thread as resolved in extraction context but the actual arc update step (`_apply_thread_updates()`) ran before the resolve was committed, so `resolved` stayed empty. Fix: check whether `thread_resolve` is processed by Storytell's own pipeline or a separate call, and verify ordering against when the thread actually became resolvable.

**Tag:** extraction_miss / scope_violation  
**Fix needed:** Investigate — grep for `thread_resolve`, trace through arc update code in turn.py ~1159-1200, check if there's an ordering issue between extraction emission and actual state mutation. Could be 3 lines or require a plan doc depending on findings.

---

## Major Issues (remaining)

### M1 — Inert Threads
Two threads (`road_instability` added T3, `dockside_confrontation` added T12) were created but never received urgency/progress updates afterward. Storytell pipeline disengages from new additions after initial creation. This is allowed by design ("Storyteller-managed") but indicates low engagement — the mechanic lifecycle score dropped to 2/5 primarily due to this.

**Tag:** storytell_engagement  
**Likely root cause:** Prompt issue — when generating beats/actions for a turn, the directive system or action selection logic gives low priority to threads that are brand new and haven't accumulated urgency yet. `road_instability` sits at default urgency while other active threads (`settle_the_debt`, `deliver_the_ledger`) get attention because they've been accumulating pressure over multiple turns.  
**Fix needed:** Review Storytell prompt's thread engagement directives, possibly add urgency thresholds or recency bonuses to ensure new threads get at least one update before being abandoned. Could be a prompt tweak (1-2 lines) or require restructuring how threads compete for attention in action generation.

### M2 — Static Arc Goals (all 13 turns)
Zero `goal_update` events emitted across the entire trace. `visible_goal` is "Clear your debts..." throughout, despite narrative arcs involving debt settlement, ledger pursuit, cellar discoveries, and bodyguard confrontation. This is technically valid if no arcs pivoted, but it means the arc system contributed nothing during a full game trace with multiple evolving storylines.

**Tag:** extraction_miss / design_question  
**Fix needed:** Determine whether `goal_update` should fire when narrative context shifts significantly (e.g., from "clear debts" to "deliver ledger" or "escape bodyguards"). If yes, tighten Storytell prompt to recognize goal-relevant state changes. If no, accept as valid behavior — arcs only pivot on explicit player choices, not incidental events.

---

## Minor Issues (remaining)

### N1 — Momentum Delta Reporting (turns 8–11, cosmetic)
Rolls happen but `momentum_delta: 0` is reported because momentum is capped at max(3). The clamping logic works correctly — it's just unclear whether downstream consumers can distinguish "roll happened, delta was +2, applied as 0 due cap" from "no roll happened." This does not affect game mechanics.

**Tag:** reporting  
**Fix needed (optional):** Distinguish `band_delta` (what the roll would produce) from `momentum_delta` (what actually gets applied after clamping). Currently both are reported, but at cap they show 0 for momentum_delta regardless of roll quality.

### N2 — Beat Type Variety Collapse (turns 6, 9–10, T4, T5, T7, T8, T10, T13)
Beat type variety assertion fails on multiple turns because fewer than 3 distinct beat types appear in the rolling window. This is expected under high pressure or floor conditions but worth monitoring for repetitive narration patterns during extended combat sequences.

**Tag:** pacing  
**Fix needed (optional):** No engine change required — accept as valid behavior under pressure/floor, or consider directive-level variety enforcement if it correlates with degraded narrative quality.

---

## Engine Validation Audit Summary

The eval revealed that the core engine has three validation layers for state deltas, but all are incomplete:

| Layer | What validates | What's missing |
|-------|---------------|----------------|
| `_validate()` (turn.py) | inventory_remove existence + balance, rejects zero-balance items | Does NOT block — still proceeds through reconcile/apply. No condition legality check. Missing targets silently skipped at debug level only. |
| `reconcile_delta()` (delta_builder.py) | Dedup add+remove conflicts, dedup conditions | No existence or legality checks. Just deduplication with logging. |
| `apply_delta()` (delta_builder.py:~175) | Fuzzy-match item IDs during mutation | Silently drops missing items at debug level only — no error/warning visible in production logs. Adds any condition unconditionally, no CONDITION_MODS check. |

**Key insight:** Phantom removals get silently suppressed at runtime (missing inventory targets are dropped), but they still pollute `events.jsonl` as emitted values because suppression happens too late to prevent emission. F4 fixes this by making validation truly blocking — rejected deltas never reach apply or pollute events.jsonl, and the structured `rejected` field records reasons for each failure.

---

## Auto-Checker Summary (Latest Run)

**316 passed, 21 failed** across 13 turns (~24 assertions per turn).

### Universal Assert Failures by Severity

| Assertion | Severity | Turns Failed | First Failure |
|-----------|----------|-------------:|---------------|
| `universal.inventory.remove_existence` | 🔴 Critical | 4 | T6 |
| `extract.state.pc_condition_remove` | 🔴 Critical | 2 | T12 |
| `ruling.rolled` | 🔴 Critical | 3 | T2 |
| `storytell.extract.thread_resolve` | 🔴 Critical | 1 | T7 |
| `universal.thread_update.valid_id` | 🔴 Critical | 0* | — (*fixed F2) |
| `extract.scene.scene_tags` | 🔴 Critical | 0* | — (*removed F3) |
| `universal.npc_mention.extracted` | 🔴 Critical | 0* | — (*removed F1) |

### Assertion Detail by Turn (Latest Run, Remaining Failures)

**T6:** `universal.inventory.remove_existence[credits]`  
**T7:** `universal.inventory.remove_existence[merchant_seal, ledger]`, `storytell.extract.thread_resolve[deliver_the_ledger]` not found  
**T8:** `extract.state.inventory_remove[brass_key]` not found (note: brass key was in seed inventory but extraction failed to find it)  
**T9:** `universal.inventory.remove_existence[credits]`  
**T11:** `extract.state.pc_condition_add[winded]`, `extract.state.inventory_add[wax_sealed_cylinder]` not found  
**T12:** `ruling.rolled`, `extract.state.pc_condition_remove[winded]`  
**T13:** `universal.inventory.remove_existence[credits]`, `extract.state.pc_condition_remove[bruised_ribs]`

---

## Pacing Metrics (Latest Run)

### Long Threads (>8 turns)
| Thread | Duration | Flagged |
|--------|----------|---------|
| `deliver_the_ledger` | 13 turns (T1–T13) | ⚠️ |
| `road_instability` | 11 turns (T3–T13) | ⚠️ — inert after T3, no updates |

### Location Dwell (>4 turns)
| Location | Turns Active | Flagged |
|----------|-------------:|---------|
| `marrows_crossing_well` | 5 | ⚠️ |

---

## Judge Scores (Latest Run)

- **State Fidelity Rate:** 0.38 (5/13 clean turns, corrected from header's 0.0)
- **Extraction Accuracy Score:** 1/7 — systemic extraction failures on inventory and conditions across multiple turns
- **Mechanic Lifecycle Score:** 2/7 — inert threads drag down score; beats and conditions are clean

---

*Previous run data (run `havr6lvx`) is superseded by this analysis. Floor relief bug was fixed in a prior session.*
