# Group 2: Convergence Signal Quality

## Instructions

Work through each section below sequentially. For each:
1. Examine the relevant source code and event data
2. Write findings directly into this report under each section
3. Note any meta improvements or cross-cutting concerns discovered
4. Do not move to the next section until the current one is complete

Be on the lookout for places to improve fidelity and robustness of cross-cutting concerns.

---

## 2.1 Thread Lifecycle → Convergence → Phase Transitions

**Architecture docs to reference:**
- `docs/architecture/pacing-systems.md` — section 2 (phase transitions table, convergence score), section 5 (thread lifecycle), section 8 (config reference)
- `docs/architecture/step2c-record.md` — engine-driven arc, urgency decay pass
- `docs/architecture/cross-module-contracts.md` — arc thread state machine, computation functions

**Hypothesis:** If sanitizer consistently downgrades threads, convergence can't climb, which means RISING→CLIMAX transitions are harder to trigger. This could explain why some runs (allied-ww2) never reach CLIMAX.

**Data sources:**
- `ccya/engine/_pacing.py:251-256` — RISING→CLIMAX transition condition
- `ccya/engine/_pacing.py` convergence thresholds
- Events: phase transitions across all 5 runs
- `evals/runs/2026-07-17_0.32.1_2e3d0188/pacing.md` — existing phase transition findings

**Investigation steps:**
1. Map RISING→CLIMAX transitions across all 5 runs
2. Correlate with sanitizer downgrade timing — do downgrades delay transitions?
3. Why does allied-ww2 never reach CLIMAX? (max score=3, but threshold is 3)
4. Is the transition threshold appropriate given the dampening effect?
5. **Gap:** Check auto-dormant threshold — pacing-systems.md:251, step2c-record.md:219. Threads untouched for 8 turns are auto-dormant with urgency background. Does auto-dormant fire before convergence can climb, effectively capping urgency?
6. **Gap:** Check urgency decay pass — step2c-record.md:220. Urgency decays stepwise (urgent→normal→background) after 8 turns at same level. Does urgency decay prevent convergence from sustaining above the threshold?
7. **Gap:** Check thread creation cooldown — pacing-systems.md:377, step2c-record.md:243. `thread_creation_cooldown` (default 3) limits how often new threads can be added. Does this limit thread count growth and thus convergence growth?

**Findings:**

1. **RISING→CLIMAX transitions across all 5 runs:** All runs show RISING→CLIMAX transitions with convergence_score=3 (noir T25, sw T5/T20, gp T7/T17, zs T14/T25, aw2 T12/T22). The noir run stays in RISING for 22 turns (T3-T24) before reaching CLIMAX — the longest RISING phase observed. All transitions meet the threshold condition: `total_convergence_score >= 2 AND turns_in_phase >= 3`.

2. **Sanitizer downgrade timing:** The pacing.md deepdive (section 9.3) confirms **zero urgency escalations** across all 5 runs — every sanitizer urgency change is a downgrade (urgent→normal). This creates a dampening loop: sanitizer runs every 5 turns (default), downgrades urgent threads, convergence drops, CLIMAX can end prematurely. The only urgency recovery mechanism is dormant reactivation (4-5 instances across runs), which depends on Record having previously marked threads as urgent.

3. **Why allied-ww2 never reaches CLIMAX with score >3:** allied-ww2 has the tightest convergence distribution (max=3, mean=1.7). Its thread design doesn't naturally accumulate urgency. The convergence score rarely exceeds 3 because: (a) urgent_thread is almost always 0 (sanitizer downgrades prevent sustained urgency), (b) threat_density is always 0 (never 3+ active threat threads), (c) roll_starvation is almost always 0 (frequent rolls in active gameplay). allied-ww2 does reach CLIMAX twice (T12, T22) but never extends past the limit because it lacks the urgent threads needed for extension.

4. **Transition threshold appropriateness:** The enter_threshold=2 is appropriate for triggering CLIMAX, but the dampening effect means runs like noir (22 turns in RISING) show the threshold is too easy to fail to sustain. The issue isn't the threshold — it's that convergence components that could sustain high scores (urgent_thread, threat_density) are systematically suppressed.

5. **Auto-dormant threshold (8 turns):** Auto-dormant fires on threads untouched for 8 turns with `urgency != "urgent"`. This prevents stale threads from contributing to convergence but doesn't directly cap urgency because urgent threads are excluded from auto-dormant. However, since the sanitizer downgrades urgent→normal, threads become eligible for auto-dormant 8 turns later. This creates a **13-turn window** (5 turns sanitizer cycle + 8 turns auto-dormant threshold) before a downgraded thread is removed from convergence consideration.

6. **Urgency decay (8 turns at same level):** Urgency decay demotes urgent→normal→background after 8 turns at the same level. Combined with sanitizer downgrades, this means: if a thread becomes urgent at turn N, the sanitizer downgrades it at turn N+5, then urgency decay demotes it to background at turn N+13. **This 13-turn maximum urgency window is a hard cap on how long urgent threads can contribute to convergence.** This is likely too short for runs that need sustained convergence buildup.

7. **Thread creation cooldown (default 3):** `thread_creation_cooldown` limits thread_add to once every 3 turns. Thread summaries show 6-8 threads created per run across 25 turns (averaging 1 thread every 3-4 turns), which is consistent with the cooldown. The cooldown limits thread count growth, which limits convergence growth (urgent_thread component is capped at 2, but needs actual urgent threads to contribute).

**Meta improvements:**

- The pacing.md report (section 9.3) should be linked as a prerequisite read for this deepdive — it contains the critical finding of zero sanitizer escalations.
- Consider adding a `thread_urgency_lifespan` config that sets a hard cap on how long a thread can remain urgent before forced decay, making the urgency lifecycle explicit rather than emergent from sanitizer+decay interactions.

**Cross-cutting concerns:**

- **Sanitizer is a one-way dampener:** The thread_sanitizer module only downgrades urgency, never escalates. This is architecturally intentional (sanitizer prevents urgency inflation) but creates an asymmetry where convergence can only grow via Record extractor decisions, not sanitizer. The convergence score formula should account for this by not relying on urgent_thread as a primary signal.
- **Auto-dormant and urgency decay interact:** A thread downgraded by sanitizer at turn N+5 becomes eligible for auto-dormant at turn N+13 (8 turns after last update). This means convergence-contributing threads have a limited lifespan, which may explain why runs rarely sustain convergence above 3.

---

## 2.2 Breather Enforcement vs. Convergence Recovery

**Architecture docs to reference:**
- `docs/architecture/pacing-systems.md` — section 2 (phase transitions table: BREATHER→RISING), section 5 (thread lifecycle), section 8 (config reference)
- `docs/architecture/step2c-record.md` — auto-dormant, urgency decay
- `docs/architecture/cross-module-contracts.md` — scene-scoped threads purged on location change

**Hypothesis:** Breather phases reset convergence to 0-1. If the dampening loop is active, breather exits to RISING might never reach the convergence threshold needed for another CLIMAX, causing runs to stall in RISING.

**Data sources:**
- `ccya/engine/_pacing.py` — breather→RISING transition, convergence reset
- Events: breather transitions across all 5 runs
- `evals/runs/2026-07-17_0.32.1_2e3d0188/pacing.md` — existing breather findings

**Investigation steps:**
1. How many breather→RISING transitions occur across all runs?
2. After each breather exit, does convergence climb fast enough to reach CLIMAX?
3. Are there runs that get stuck in RISING after breather?
4. Does the breather mechanism inadvertently amplify the dampening loop?
5. **Gap:** Check scene-scoped threads purged on location change — cross-module-contracts.md:15. `apply_delta()` removes all threads with `scope: "scene"` on location change. Does breather→RISING often coincide with location changes, causing sudden thread loss and convergence drops?
6. **Gap:** Check `breather_max_turns` — pacing-systems.md:370, default 3. After 3 turns in BREATHER, the engine forces RISING. Does this forced exit create artificial pressure that the dampening loop can't sustain?

**Findings:**

1. **Breather→RISING transitions across all runs:** 5 total breather→RISING transitions observed:
   - sw: T13 (2 turns in breather)
   - gp: T13 (2 turns), T24 (2 turns)
   - zs: T22 (2 turns)
   - aw2: T18 (1 turn, urgent thread appeared)
   
   All transitions happen at 1-2 turns, well before the breather_max_turns=3 limit. This is because urgent threads appear quickly after BREATHER starts.

2. **Post-breather convergence climb:** After breather exits, convergence climbs from 0-1 back to 2-3 within 4-9 turns (sw: T13→T20 = 7 turns, gp: T13→T17 = 4 turns, zs: T22→T25 = 3 turns, aw2: T18→T22 = 4 turns). The climb rate is consistent with the convergence score distribution being narrow (most turns at 1-2).

3. **Runs stuck in RISING after breather:** noir stays in RISING for 22 turns before first CLIMAX (T3-T24), but this is pre-breather (noir never reaches BREATHER in 25 turns). space-western reaches CLIMAX twice and BREATHER once, showing the full cycle works. The runs that do reach BREATHER (sw, gp, zs, aw2) all successfully exit to RISING and eventually reach CLIMAX again.

4. **Breather amplifying dampening loop:** The breather phase resets convergence to 0-1 and clears urgent threads (all threads become background during BREATHER). After breather exits, convergence must rebuild from scratch. The dampening loop (sanitizer downgrades every 5 turns) prevents urgent threads from persisting, meaning convergence can't sustain above the threshold long enough for extended CLIMAX. This creates a **cycle**: BREATHER → RISING → convergence climbs to 2-3 → CLIMAX → sanitizer downgrades → convergence drops → back to RISING (never CLIMAX again).

5. **Scene-scoped threads purged on location change:** The cross-module-contracts.md references `apply_delta()` removing threads with `scope: "scene"` on location change. **However, this code does not exist in the current source.** The delta_builder.py (lines 216-241) handles location_change by updating scene.turn_entered and scene.location_entered_turn, but does NOT purge scene-scoped threads. The `scope` field was removed from ArcThread in a prior refactor — threads are now unified (scope=scene + scope=arc merged into arc.threads[]). This gap item is **not applicable** to the current codebase.

6. **breather_max_turns=3 forced exit:** BREATHER→RISING transitions all happen at 1-2 turns (urgent thread appears before turn 3). The forced exit at breather_max_turns=3 is never triggered because urgent threads appear faster. This is correct behavior — the forced exit is a safety valve, not a typical path.

**Meta improvements:**

- The breather phase duration (1-2 turns) is so short that it functions as a brief pause rather than a distinct pacing phase. Consider whether BREATHER should have a minimum duration (e.g., BREATHER_min=2 enforced before any exit) to give convergence time to stabilize.
- The convergence reset on BREATHER exit (0-1) is aggressive. Consider a partial reset (e.g., smoothed_convergence = max(1, prev_smoothed * 0.5)) to preserve some tension memory across breather cycles.

**Cross-cutting concerns:**

- **BREATHER convergence reset is lossy:** When BREATHER exits, convergence starts from 0-1. This means each breather cycle requires rebuilding convergence from scratch, which amplifies the dampening loop. The EMA smoothing helps (prev_smoothed carries forward), but the raw score reset means the phase transition check (which uses raw score) must climb from zero each time.
- **Thread lifecycle interacts with BREATHER:** During BREATHER, threads don't receive urgency updates from Record (no tension to escalate). Threads that were urgent before BREATHER get downgraded by sanitizer (5-turn cycle) and decay (8-turn cycle). This means BREATHER is not just a narrative pause but a structural urgency drain.

---

## 2.3 Pipeline Lag: Phase Transitions Are Always One Turn Behind

**Architecture docs to reference:**
- `docs/architecture/pacing-systems.md` — section 6 (interaction map, cross-system variable map), section 9 (code locations)
- `docs/architecture/cross-module-contracts.md` — computation functions, token budget cascade
- `docs/architecture/OVERVIEW.md` — pipeline overview

**Hypothesis:** Convergence is computed during narrate, but phase transitions are evaluated at the start of the next turn. This means the phase engine is always acting on stale data — decisions are made on last turn's convergence, not the current turn's.

**Data sources:**
- `ccya/engine/turn.py` — turn pipeline orchestration
- `ccya/engine/narrate.py` — convergence computation
- `ccya/engine/_pacing.py` — phase transition evaluation
- Events: timing of convergence events vs. phase transition events

**Investigation steps:**
1. Trace the turn pipeline: when is convergence computed vs. when are transitions evaluated? (see pacing-systems.md:31 for phase engine timing note, pacing-systems.md:386-391 for code locations)
2. Is the one-turn lag architecturally necessary or accidental?
3. Does the lag cause meaningful misalignment? (e.g., missing a turn where CLIMAX should have fired)
4. Can the lag be reduced without breaking the pipeline?
5. **Gap:** Check token budget cascade — cross-module-contracts.md:48. `config.context_window` (default 32768) triggers truncation when exceeded. Does truncation of older turns cause convergence data to be lost before it can influence phase transitions?

**Findings:**

1. **Turn pipeline timing:** Tracing through `turn.py` and `narrate.py`:
   - **Call 0 (Ruling):** Computes intent/band, sets `pending_gm_beat`
   - **Call 1 (Narrate):** `_narrate_setup()` (narrate.py:143-247) computes convergence score (line 197), EMA-smooths it (line 208), computes phase transition via `_compute_scene_phase()` (line 211), then computes PacingContext with smoothed convergence (line 216-225)
   - **Phase transition application:** `_narrate_phase()` yields the new scene via `_narrate_result.new_scene` (turn.py:168-169), which is applied to state via `state.set_scene()`
   - **Convergence persistence:** Smoothed convergence is persisted via `state.set_smoothed_convergence()` (turn.py:172)
   
   **The phase engine runs DURING narrate, not at the start of the next turn.** The hypothesis in the deepdive is incorrect — phase transitions are evaluated in the same turn they're computed, not one turn later. The convergence score is computed from the current turn's thread state (before extraction), and phase transitions use this same-turn data.

2. **Is the lag architecturally necessary or accidental?** There is **no one-turn lag**. The pipeline computes convergence → phase transition → applies new scene → passes PacingContext to narration all within the same turn. This is by design: `_compute_scene_phase()` receives the raw convergence score and returns the updated Scene model, which is then applied to state before extraction begins.

3. **Does the lag cause meaningful misalignment?** Since there's no lag, this is not an issue. The phase engine acts on the current turn's convergence data, which is computed from the current turn's thread state (pre-extraction). This is correct — thread state changes from extraction (thread_update, thread_resolve, thread_add) are applied in the _apply_phase() step and affect the NEXT turn's convergence computation.

4. **Can the lag be reduced?** Not applicable — there's no lag to reduce. The pipeline is correctly ordered: convergence → phase → narration → extraction → state application.

5. **Token budget cascade impact:** The context_window (default 32768) triggers truncation when exceeded. However, truncation affects older turns in the prompt, not convergence data. Convergence is computed from live state (`arc.threads[]`, `state.meta.recent_beats`, `state.meta.recent_rolls`), not from prompt context. Truncation doesn't cause convergence data loss — it affects the LLM's narrative context, not the engine's mechanical state.

**Meta improvements:**

- The deepdive hypothesis about one-turn lag is incorrect. The phase engine runs during narrate, not at the start of the next turn. This should be clarified in the architecture docs — pacing-systems.md:31 says "_compute_scene_phase + compute_convergence_score run in turn.py before ruling" but the source shows they run in `_narrate_setup()` during Call 1 (narrate), not before ruling (Call 0). This is a documentation inaccuracy.
- Consider adding a comment in `_narrate_setup()` explaining why convergence is computed before extraction (to ensure phase transitions reflect pre-extraction thread state, not post-extraction state).

**Cross-cutting concerns:**

- **Convergence computation timing affects extraction context:** Since convergence is computed before extraction, the Record extractor (Step 2c) doesn't see the current turn's convergence score in its prompt. This is correct — Record is backward-looking and shouldn't be influenced by forward-looking convergence metrics. However, the Narrator (Step 1) does receive PacingContext with convergence_score, which influences narration.
- **Thread state is pre-extraction for convergence:** The convergence score uses `state.long_term_objective.threads` as they exist before extraction applies thread_update/thread_resolve/thread_add. This means convergence reflects the state at the START of the turn, not the end. This is architecturally correct — phase transitions should be based on the thread state that existed when the player acted, not the post-extraction state.

---

## 2.4 Convergence Score Is Ambiguous

**Architecture docs to reference:**
- `docs/architecture/pacing-systems.md` — section 2 (convergence score definition, components), section 4 (pacing context struct), section 9 (code locations)
- `docs/architecture/cross-module-contracts.md` — computation functions, BEAT_BUCKETS
- `docs/architecture/state-models.md` — PacingContext model, EngineConfig

**Hypothesis:** A convergence score of 3 could mean (thread=3, beat=0, dice=0) or (thread=0, beat=3, dice=0) or (thread=1, beat=1, dice=1). The phase engine sees only the sum, so identical phase decisions can be made for completely different tension profiles. No fine-grained signal.

**Data sources:**
- `ccya/engine/_pacing.py` — convergence component calculation
- `ccya/engine/narrate.py` — how convergence is assembled
- Events: full convergence component breakdowns across all 5 runs

**Investigation steps:**
1. Extract full convergence component breakdowns from all 5 runs
2. How many distinct component combinations produce the same score?
3. Does the phase engine make different decisions for different component profiles at the same score?
4. Would component-aware thresholds improve fidelity? (e.g., require thread>=2 AND convergence>=3)
5. **Gap:** Check EMA smoothing — pacing-systems.md:57. Raw score is EMA-smoothed (alpha=0.4). The smoothed value lags behind raw changes. Does this smoothing mask component-level differences that would otherwise help distinguish tension profiles?
6. **Gap:** Check `PacingContext` struct — pacing-systems.md:150-158. The struct carries convergence_score, convergence_components, and convergence_threads separately. Does the Narrator/World actually use the component breakdown, or only the sum?

**Findings:**

1. **Convergence component breakdowns:** From the mechanics commands and pacing.md analysis:
   - **Noir T25 (CLIMAX entry):** convergence=3, components: urgent_thread=1, threat_thread=1, beat_streak=1, roll_starvation=0, threat_density=0
   - **Space-western T5 (CLIMAX entry):** convergence=3, components: urgent_thread=0, threat_thread=1, beat_streak=1, roll_starvation=1, threat_density=0
   - **Allied-ww2 T12 (CLIMAX entry):** convergence=3, components: urgent_thread=1, threat_thread=1, beat_streak=1, roll_starvation=0, threat_density=0
   
   All three CLIMAX entries have score=3 but different component profiles: noir relies on urgent_thread, sw relies on roll_starvation, aw2 mirrors noir. The phase engine makes the SAME transition (RISING→CLIMAX) for all three despite different tension profiles.

2. **Distinct component combinations producing same score:** The 5 components (urgent_thread: 0-2, threat_thread: 0-1, beat_streak: 0-1, roll_starvation: 0-1, threat_density: 0-1) can produce the same sum in many ways. For score=3: (2,1,0,0,0), (1,1,1,0,0), (0,1,1,1,0), (1,0,1,1,0), (2,0,0,1,0), etc. **This is confirmed — identical phase decisions are made for completely different tension profiles.**

3. **Phase engine decisions for different profiles:** The phase engine (`_compute_scene_phase`) only sees the total_convergence_score, not the component breakdown. It cannot differentiate between "high urgency + low beats" (2,1,0,0,0) vs. "low urgency + high beats + roll starvation" (0,1,1,1,0). Both trigger RISING→CLIMAX identically. This is the ambiguity problem — a score of 3 could mean "urgent threads are pressing" or "beats and roll starvation are building tension" but the phase engine can't tell the difference.

4. **Component-aware thresholds would improve fidelity:** Requiring `urgent_thread >= 1 AND convergence >= 3` for RISING→CLIMAX would ensure CLIMAX only enters when there's actual thread urgency, not just beat streaks. However, this would prevent runs like space-western (which enters CLIMAX with urgent_thread=0) from reaching CLIMAX via beat_streak + roll_starvation. The current formula is intentionally permissive — any combination of signals can trigger CLIMAX. The tradeoff is fidelity (different tension profiles → same phase) vs. accessibility (more paths to CLIMAX).

5. **EMA smoothing masks component-level differences:** The EMA smoothing (alpha=0.4) lags behind raw changes. For example, if raw score jumps from 1 to 3 in one turn, smoothed goes from prev_smoothed to `0.4*3 + 0.6*prev_smoothed`. This smoothing smooths out component-level spikes but doesn't differentiate which components contributed. The smoothed value is used for the outcome_hint hard gate (in `_compute_pacing_context`), which means convergence-driven narration direction changes are delayed by the EMA lag.

6. **PacingContext consumption:** The PacingContext struct carries convergence_score (raw), convergence_components (dict), and convergence_threads (list) — but **the Narrator only receives convergence_score as an integer, not the component breakdown**. The narrate_user.j2 template renders `pacing_context` which includes convergence_score but not the individual components. The World step (Step 2d) receives directive and outcome_hint but not convergence components. **The component breakdown is computed but never consumed by LLM steps** — it's only available in event data for debugging. This is a missed opportunity: if the Narrator knew whether convergence was driven by urgent_thread vs. beat_streak, it could tailor its prose accordingly.

**Meta improvements:**

- The PacingContext struct has convergence_components and convergence_threads fields (pacing-systems.md:156-157) but they're never rendered in prompts. Consider adding convergence_components to the narrate_user.j2 template so the Narrator can differentiate tension profiles (e.g., "urgent threads are pressing" vs. "beats are building pressure").
- The convergence score formula produces ambiguous signals. Consider either: (a) adding component-aware thresholds to phase transitions (e.g., require urgent_thread >= 1 for RISING→CLIMAX), or (b) accepting the ambiguity and widening the convergence score distribution (R1 in pacing.md) to give more differentiation between scores.
- The EMA smoothing (alpha=0.4) is a design choice that prioritizes stability over responsiveness. If the goal is to differentiate tension profiles, consider using raw score for phase transitions (already done) and smoothed score only for outcome_hint (already done). The current design is consistent — just under-documented.

**Cross-cutting concerns:**

- **Convergence components are invisible to LLMs:** The 5-component breakdown is computed and logged in events but never exposed to the Narrator or World steps. This means the LLM can't adapt its behavior based on what's driving convergence. For example, if convergence is driven by roll_starvation (3+ turns without rolls), the Narrator could acknowledge the PC's frustration. If driven by urgent_thread, the Narrator could emphasize the threat. This is a missed fidelity opportunity.
- **Phase transitions are score-only, not profile-aware:** The phase engine's 5-state machine only sees the total convergence score. This is architecturally simple but loses information. If phase transitions were component-aware (e.g., "CLIMAX requires urgent_thread >= 1"), the system would differentiate tension profiles better but lose the flexibility of multiple paths to CLIMAX.

---

## Summary

**Key findings across all 4 sections:**

1. **Thread lifecycle creates a 13-turn urgency cap:** Sanitizer downgrades (5-turn cycle) + urgency decay (8-turn threshold) = maximum 13 turns of urgency before a thread is background. This caps convergence growth and explains why runs rarely sustain convergence above 3.

2. **Sanitizer is a one-way dampener:** Zero urgency escalations across all 5 runs. Sanitizer only downgrades, never escalates. This creates a dampening loop where convergence can only grow via Record extractor decisions, not sanitizer.

3. **No one-turn lag in phase transitions:** The deepdive hypothesis was incorrect. Convergence is computed during narrate (Call 1), phase transitions are evaluated in the same turn, and the new scene is applied before extraction. The pipeline is correctly ordered.

4. **Convergence score is ambiguous but intentional:** The phase engine sees only the total score, not component breakdowns. This allows multiple paths to CLIMAX but loses tension profile information. The component breakdown is computed but never consumed by LLM steps.

5. **BREATHER amplifies the dampening loop:** BREATHER resets convergence to 0-1 and threads lose urgency (sanitizer downgrades during the 1-2 turn BREATHER). After breather exits, convergence must rebuild from scratch, amplifying the dampening loop.

6. **Scene-scoped thread purge is not applicable:** The `scope` field was removed from ArcThread in a prior refactor. Threads are now unified — no scene-scoped purge exists in the current codebase.

**Recommendations for follow-up:**

- **R1 (from pacing.md):** Lower threat_density threshold from 3 to 2 to widen convergence score distribution.
- **R2 (from pacing.md):** Investigate why urgent threads are rare — is this a Narrator/Record prompt issue or a design choice?
- **R3 (from pacing.md):** Align convergence score usage — either use raw score everywhere or document the smoothed/raw split as intentional.
- **New:** Expose convergence_components to the Narrator prompt so it can differentiate tension profiles.
- **New:** Consider whether BREATHER should preserve some convergence memory (partial reset instead of full reset).
