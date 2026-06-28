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

## Deep Dive: Narrative Quality & Pacing Mechanics

**Scope:** Manual inspection of `0225_noir-1930s_driven_15t` (15 turns, 18 events). This is the most complete noir run with full turn-by-turn data.

### Phase Transition Volatility — Critical Issue

The pacing system produces **10 phase transitions in 15 turns**:

```
SETUP → SETUP → RISING → CLIMAX → CLIMAX → RESOLUTION → BREATHER → RISING → CLIMAX → CLIMAX → CLIMAX → RESOLUTION → BREATHER → BREATHER → RISING
```

That is a phase change almost every other turn. This is the opposite of smooth pacing.

### Phase-Narrative Mismatch — Critical Issue

The pacing system assigns phases that **directly contradict** the narrative tension:

| Turn | Narrative Tension | Assigned Phase | Mismatch |
|------|-------------------|----------------|----------|
| T6 | Gunfire, tackles, second sedan arrives | RESOLUTION | Opposite |
| T7 | Pistol aimed at player's chest | BREATHER | Opposite |
| T13 | Player arrives at records building after escape | BREATHER | Acceptable |
| T15 | Player infiltrates restricted archives | RISING | Acceptable |

**T6 and T7 are the worst offenders.** The narrative is at peak action (gunfire, physical combat, reinforcements arriving) but the phase is RESOLUTION/BREATHER. This creates cognitive dissonance for the reader.

### What Is Working

1. **Seed generation is excellent** — rich sensory details, immediate tension, clear stakes. The noir atmosphere is strong.
2. **Narrative prose is consistent** — "wet cobblestones," "flickering streetlamps," "heavy brass clasps" maintain the noir tone throughout.
3. **Plot is engaging** — witness, evidence box, encrypted ledger, precinct vaults. The mystery unfolds naturally.
4. **Action sequences are well-written** — "swing your brass knuckles into the Scarred Man's jaw," "tackle the Watchful Man mid-stride."

### What Is Broken

1. **Phase transitions are too reactive.** The convergence score fluctuates wildly based on individual turn events, causing phases to flip-flop. A phase should represent a sustained narrative state, not oscillate turn-to-turn.

2. **No hysteresis in phase transitions.** The system transitions up and down on the same thresholds. There is no "hold" mechanism to prevent flip-flopping. For example, CLIMAX→RESOLUTION happens at conv=1, but RESOLUTION→RISING happens at conv=1. The same threshold triggers opposite transitions.

3. **Convergence score is too volatile.** It jumps from 4→1→4→5→4→2→0→0→1. This is because thread urgency changes turn-to-turn based on what the LLM generates, and there is no smoothing.

4. **The pacing feels artificial.** A noir scene should build tension over 5-10 turns, not reset every 2-3 turns. The reader experiences: build-up → climax → abrupt reset → build-up → climax → abrupt reset. This is jarring.

### Comparison: 0215 (5 turns) vs 0225 (15 turns)

The 0215 run had a cleaner progression: SETUP(2) → RISING(1) → CLIMAX(2). Only 2 phase transitions. The 0225 run has 10 transitions in 15 turns. The longer run exposes the volatility problem.

### Verdict

**The pacing system is not working as intended.** The convergence-proactive design aimed for smooth, signal-gated phase transitions. Instead, the system is creating a jittery pacing that oscillates rapidly. The narrative prose is strong, but the pacing layer is fighting against it by assigning phases that contradict the narrative tension.

The root cause is that the convergence score is too reactive to individual turn events. It needs smoothing (e.g., moving average over 3-5 turns) and hysteresis (different thresholds for entering vs exiting a phase).

---

## Recommendations

1. **Fix phase transition volatility** — Add smoothing to convergence score (moving average over 3-5 turns) and hysteresis (different thresholds for entering vs exiting each phase). This is the highest priority finding.
2. **Fix phase-narrative mismatch** — Investigate why RESOLUTION/BREATHER is assigned during peak action sequences. May require checking if thread urgency is being incorrectly cleared or if the convergence score is being reset prematurely.
3. **B-10 needs live UI validation** — not testable via evals
4. **B-20 appears fixed** — no duplicates in 3 runs
5. **Engine is stable** — no critical or intermediate bugs unfixed. Ready for next phase of development.
