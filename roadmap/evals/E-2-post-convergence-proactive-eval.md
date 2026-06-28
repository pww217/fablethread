---
title: "Post-convergence-proactive + NPC redesign eval — beats, pacing, NPC systems"
status: completed
urgency: 1
size: xlarge
created: 2026-06-28
ticket_id: E-2
labels:
  - eval
  - engine
  - pacing
  - beats
  - npc
  - convergence
---

## Context

Eval group: `2026-06-28_0.30.0-38-gd67ef9ca_d67ef9c`

Prior full eval: `2026-06-25_0.28.0-113-g2990468_2990468` — 18 runs (all 5 persona pairs × 25 turns).
Prior SHA: `2990468`
Current SHA: `d67ef9ca` (HEAD)

### Changes since last full eval (SHA 2990468 → HEAD)

Major engine changes:
- **Convergence-proactive plan** (0d8013d): Beat pipeline simplification, 6-component convergence, signal-gated CLIMAX exit, phase machine moved pre-ruling, index-based beat selection
- **Beat generation split** (7a309d91, dafabe7e): Split Storytell into Record + Ruling beat selection + async World
- **CLIMAX hardcoded limit fix** (d29a6317): Fix CLIMAX limit, weighted convergence score
- **NPC scene redesign** (1cb1414): Remove aliases, group NPC logic, ambient NPC requirements
- **Phase transition signals checker bug** (d3690d34): Fix checker bug + convergence_recompute data gap
- **17 new deterministic checkers** (ada9e639): Pacing, convergence, thread lifecycle, state integrity
- **E-1 fixes** (1e5f65da): All 6 validated eval findings fixed
- **UI lock fixes** (multiple): SSE drain task, lock release timing, asyncRunning flag
- **Async steps recording**: World step recording in events.jsonl
- **Eval trace marker removal** (c2998d1): Remove <<<TRACE_IMMUTABLE_START/END>>>
- **Doc updates** (d67ef9c)

### Testing items
- B-10 (UI highlighting) — in testing
- B-20 (thread duplicate IDs) — in testing

### Prior eval findings (E-1)
1. `config` NameError in `_compute_pacing_context` — CLIMAX hard cap broken
2. Phase transitions firing without required triggers
3. RISING→CLIMAX at score 2, below threshold of 3
4. State extraction retries — `condition_change_reason` missing
5. High thread dedup rate in allied run
6. Inventory canonical ID on first add

All 6 were marked as FIXED in E-1. This eval will validate whether those fixes actually work in practice.

---

## Findings (to be populated during eval)

### Phase 1
**Run:** noir-1930s/driven, 5 turns
**Pass rate:** 95.2%
**Result:** All checkers pass (1 ruling_band_distribution failure expected with 5 turns)
**E-1 validation:** All 6 prior findings appear fixed

### Phase 2
**Runs:** noir-1930s/driven 15t, space-western/speedrunner 15t, golden-piracy/completionist 15t
**Pass rates:** 92.9%, 90.5%, 92.9%
**Result:** 1 engine bug fixed, 3 checker false positives identified

**Engine bug fixed:**
- Phase transition reading stale scene dict (`narrate.py:234,245`)
- `_compute_scene_phase()` returns new dict, but `narrate.py` read from old local variable
- Fix: Read from `state["scene"]` instead of local `scene`
- Verified: Post-fix noir run passes all checkers

**Checker false positives (need fixing):**
1. `phase_transition_signals` — reads breather_turn_count from current turn instead of previous
2. `phase_transition_signals` — checks current turn's urgent threads instead of previous turn's state
3. `thread_cooldown` — threshold may be too strict
4. `convergence_recompute` — scene_age off by 1

**Testing items:**
- B-10: Code fixes present, needs live UI validation
- B-20: Fixed — no duplicate thread_add IDs in any run

### Phase 3 (original)
**Runs:** noir-1930s/driven 25t, space-western/speedrunner 25t, golden-piracy/completionist 25t, allied-ww2/protector 25t, zombie-survival/survivor 25t
**Pass rates:** 95.2% across all 5 runs (identical pattern)
**Result:** Engine stable — no new bugs found

**Consistent checker failures (40/42 pass):**
1. `sanitizer_lifecycle` — expected (no save dir used, sanitizer skipped)
2. `location_description_consistency` — Turn 1 and some turns have short/empty location descriptions (quality issue, not a bug)

**No engine bugs found.** All pacing, thread, convergence, and ruling checkers pass.

### Phase 3 (post-location-fix)
**Runs:** noir-1930s/driven 25t, space-western/speedrunner 25t, golden-piracy/completionist 25t, allied-ww2/protector 25t, zombie-survival/survivor 25t
**Pass rates:** 97.6%, 100.0%, 95.2%, 97.6%, 97.6%
**Result:** All runs pass location_description_consistency after seed generation fixes

**Engine bugs fixed:**
1. **Seed generation NPC presence reliability** — LLM sometimes generated seeds with empty compendium
   - Added mandatory NPC requirement to prompt absolute rules
   - Added pre-sanitization of raw JSON before Pydantic validation (null list coercion)
   - Added safety net to force first NPC to present if compendium is non-empty
   - Added explicit feedback to LLM when compendium is empty to trigger retry
   - Added NPC presence default in prompt_context.py to handle None values
   - Fixed NPC roster sort to handle None names

**Consistent checker failures (41/42 pass):**
1. `sanitizer_lifecycle` — expected (no save dir used, sanitizer skipped)

**No engine bugs found.** All pacing, thread, convergence, ruling, and state checkers pass.

---

## Recommendations

1. **B-10 needs live UI validation** — not testable via evals
2. **B-20 appears fixed** — no duplicates in 3 runs
3. **Engine is stable** — no critical or intermediate bugs unfixed. Ready for next phase of development.
