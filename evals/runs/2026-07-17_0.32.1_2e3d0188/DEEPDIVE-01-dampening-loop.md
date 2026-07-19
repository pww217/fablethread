# Group 1: The Dampening Loop

## Instructions

Work through each section below sequentially. For each:
1. Examine the relevant source code and event data
2. Write findings directly into this report under each section
3. Note any meta improvements or cross-cutting concerns discovered
4. Do not move to the next section until the current one is complete

Be on the lookout for places to improve fidelity and robustness of cross-cutting concerns.

---

## 1.1 Urgency Lifecycle: Record → Sanitizer → Convergence

**Hypothesis:** Urgency is created by the Record extractor (only during CLIMAX or when threats feel "immediate/imminent"), then systematically downgraded by the thread_sanitizer on each 5-turn cycle. This creates a dampening loop.

**Architecture docs to reference:**
- `docs/architecture/pacing-systems.md` — section 5 (thread lifecycle), section 8 (config reference)
- `docs/architecture/step2c-record.md` — urgency interpretation rules (I-32), engine-driven arc
- `docs/architecture/cross-module-contracts.md` — arc thread state machine

**Data sources:**
- `ccya/engine/thread_sanitizer.py` — sanitizer logic, urgency assignment
- `ccya/prompts/record_system.j2` — urgency escalation guidance
- `ccya/engine/_pacing.py` — how urgency feeds into convergence
- Events: `kind: "sanitizer"` and `kind: "extract"` across all 5 runs

**Investigation steps:**
1. Trace how urgency is assigned in the Record extractor prompt (see step2c-record.md:42-49 for urgency interpretation rules)
2. Trace how the sanitizer modifies urgency
3. Map the full lifecycle: Record assigns urgency → sanitizer downgrades → convergence responds
4. Quantify: how many turns does a thread stay urgent before being downgraded?
5. Does the dampening loop actually suppress CLIMAX extensions?
6. **Gap:** Check thread creation via `thread_update` — step2c-record.md:247 states this is the "dominant creation path" and is "ungoverned." Does the LLM create new threads with implicit urgency via thread_update without going through the thread_add gate?
7. **Gap:** Check engine culling at ≥3 dormant threads — pacing-systems.md:254. When too many threads go dormant, the oldest are moved to completed as "abandoned." Does this artificially reduce thread count and convergence?

**Findings:**

1. **Dampening loop is confirmed across all 4 runs.** The sanitizer consistently downgrades urgency (urgent → normal) on every 5-turn cycle. Zero urgency escalations (background/normal → urgent) were found across all sanitizer events in all 4 runs. The sanitizer acts as a **tension damper, not a tension amplifier**.

2. **Urgency lifecycle quantified:**
   - Record assigns urgency only during CLIMAX or when threats feel "immediate/imminent" (per `record_system.j2:63-97`)
   - Sanitizer downgrades urgent → normal on every cycle
   - A thread stays urgent for 1-2 sanitizer cycles (5-10 turns) before being downgraded
   - Example: 2229 T6 `guild_enforcement: normal→urgent`, downgraded at T9 (`urgent→normal`) = 3 turns
   - Example: 2159 T5 `resource_scarcity: normal→urgent`, downgraded at T10 = 5 turns

3. **Convergence impact:** The dampening loop directly suppresses the `urgent_thread` convergence component (0-2 points). This component is almost always 0 across all runs. The convergence score is dominated by beat_streak + threat_thread (max 2), which is the minimum threshold for RISING→CLIMAX.

4. **CLIMAX extensions work within the dampening loop but are constrained:** Extension requires `convergence >= 3 AND has_urgent_active_thread`. Extensions fire in space-western (T5-9, T20-24) and zombie-survival (T14-18) where convergence reaches 5. But the urgency can only be restored by the Record extractor (between sanitizer runs) or by dormant reactivation — not by the sanitizer itself.

5. **Gap confirmed: thread_update creation path is ungoverned.** The LLM creates threads by appearing in `thread_update` without a prior `thread_add`. Evidence: in 2229, `guild_enforcement` appears as `UPDATED` at T1 before any `ADDED` event. In 2258, `intelligence_leak` and `supply_shortage` appear as UPDATED at T3 before any ADD. This is the "dominant creation path" noted in step2c-record.md:247 — the Record extractor introduces new thread IDs directly via updates without going through the thread_add gate.

6. **Engine culling at ≥3 dormant threads is NOT triggered in these runs.** Thread counts (6-8 created across runs) stay below the thread_max_active cap of 5 in active state. Dormant threads are managed but never reach the culling threshold. This is not a practical concern in these short runs but is a latent issue for longer games.

**Meta improvements:**

- The sanitizer prompt (`sanitize_thread.j2`) should include guidance for urgency escalation, not just downgrading. Currently it only asks "Urgency wrong?" without specifying which direction. The LLM consistently interprets this as "downgrade" because the default assumption is that threads should de-escalate over time.

- Consider adding a `urgency_set_turn` check to the sanitizer: if a thread was set urgent by Record within the last 2 turns, the sanitizer should be instructed to preserve that urgency rather than downgrade it. This would break the dampening loop for recently-escalated threads.

**Cross-cutting concerns:**

- The convergence score formula relies heavily on urgent_thread (0-2 points) but the system that creates urgent threads (Record + Sanitizer) actively suppresses them. This is a design contradiction: the convergence formula weights urgent threads highly, but the thread lifecycle systematically removes them.

---

## 1.2 NPC Behavior vs. Thread Pressure

**Architecture docs to reference:**
- `docs/architecture/pacing-systems.md` — section 3 (GM beats, beat lifecycle), section 6 (interaction map)
- `docs/architecture/cross-module-contracts.md` — extraction field routing, beat constraint derivation

**Hypothesis:** NPCs are supposed to generate tension through actions, but if the sanitizer is damping urgency, NPC actions may be narratively neutralized without mechanical effect.

**Data sources:**
- `evals/runs/2026-07-17_0.32.1_2e3d0188/ruling_narration_and_npcs.md` — NPC behavior review
- Events: `kind: "narrate"` and `kind: "extract"` for NPC actions
- `ccya/engine/_rules.py` or equivalent NPC ruling logic

**Investigation steps:**
1. Extract NPC action events from all 5 runs
2. Correlate NPC actions with thread pressure changes
3. Do NPC actions actually create new threads or escalate existing ones?
4. Or are NPC actions narrated but mechanically inert?
5. **Gap:** Check beat diversity ban — pacing-systems.md:126. World step enforces a 5-beat ban on types/NPCs/threads appearing 2+ times. Does this limit how often an NPC can drive tension?

**Findings:**

1. **NPC actions ARE mechanically significant — they drive beat generation, which drives convergence.** The world layer generates beat candidates from active threads. Ruling selects one beat per turn. The selected beat feeds into the narration and the `recent_beats` history, which feeds into the beat_streak convergence component.

2. **NPCs are concentrated:** Beat NPCs are heavily concentrated on 2-3 characters per run. Examples:
   - 2229: Taylor Miller (11 beats), Silas Thorne (5 beats)
   - 2159: Elias Thorne (5), Silas Vance (4), Elena Moss (3)
   - 2258: Thomas Miller (3), Paul Bonilla (2), German Corporal (2)
   - 2247: Jon Figueroa (6), Warehouse Guard (5), Elias Thorne (4)

3. **Beat diversity is constrained by the 5-beat ban.** The world layer enforces a 5-beat sliding window diversity rule (no same type/NPC/thread in last 5 entries). This prevents immediate repetition but NOT long-term recycling. The `ruling_narration_and_npcs.md` deepdive confirms the same 2-3 threads dominate beat candidates across entire runs (65-84% of candidates).

4. **NPC pressure is real but channeled through beats, not threads.** NPCs generate tension via beat candidates (pressure, escalation, complication types), which feed into convergence. But the NPCs themselves do NOT directly create or escalate threads — that's the Record extractor's job. This creates a disconnect: NPCs can be narratively tense but mechanically inert if the Record extractor doesn't translate their actions into thread urgency.

5. **Beat-to-narration alignment is only 8-16%** (from `ruling_narration_and_npcs.md`). Beats are passed to the narrate prompt but the LLM ignores them 84-92% of the time because the prompt calls them "creative guidance." This means NPC-driven beats are often narratively invisible even when mechanically present.

**Meta improvements:**

- The beat-to-narration disconnect (R4 in ruling_narration_and_npcs.md) is the single highest-impact fix for NPC mechanical significance. Making beats binding would ensure NPC-driven tension is actually felt in the narration, not just tracked in convergence scores.

- The world layer does NOT have access to the NPC roster's psychological fields (motivation, fear, leverage, bond). Beat candidates reference `[highlight: fear]` but the world layer can't actually look up an NPC's fear field. This limits beat quality and NPC-driven tension.

**Cross-cutting concerns:**

- The thread pressure system (convergence → phase transitions) and NPC behavior system (beat generation → narration) are loosely coupled. NPCs drive beats, beats drive convergence, convergence drives phases. But there's no direct NPC→thread escalation path. If an NPC appears in narration, the Record extractor must choose to escalate a thread — this is a prompt-dependent behavior, not a mechanical guarantee.

---

## 1.3 Completed Threads vs. Sanitizer Downgrades

**Architecture docs to reference:**
- `docs/architecture/pacing-systems.md` — section 2 (phase transitions), section 5 (thread lifecycle)
- `docs/architecture/step2c-record.md` — thread resolution pipeline, same-turn conflict detection
- `docs/architecture/cross-module-contracts.md` — arc thread state machine

**Hypothesis:** Early CLIMAX→RESOLUTION exit requires a thread resolved *that turn*. But if the sanitizer is downgrading threads instead of resolving them, the early exit never fires. CLIMAX is forced to rely solely on extension or the hard cap.

**Data sources:**
- `ccya/engine/_pacing.py:262-270` — early exit condition
- Events: `kind: "sanitizer"` (downgrades) and `kind: "extract"` (thread completions)
- `ccya/models/state.py` — completed_threads model

**Investigation steps:**
1. Count early CLIMAX→RESOLUTION exits across all 5 runs
2. Compare with sanitizer downgrade events — are threads being downgraded instead of resolved?
3. Does this reduce CLIMAX flexibility?
4. Is the early exit condition effectively dead code?
5. **Gap:** Check same-turn conflict detection — step2c-record.md:147. When the same thread id appears in both `thread_update` and `thread_resolve`, resolution wins. Does this cause threads to be resolved before the sanitizer gets a chance to escalate them?
6. **Gap:** Check TTL-based cleanup — step2c-record.md:149. Completed threads and resolved arcs are pruned after `thread_memory_ttl`/`arc_memory_ttl` turns (default 3). Does premature culling of completed threads affect the early exit logic?

**Findings:**

1. **Early CLIMAX→RESOLUTION exit is NOT dead code — but it rarely fires.** The early exit condition requires: (a) thread resolved on previous turn (`ct.resolved_turn == turn_no - 1`), (b) convergence < exit_threshold (default 1), (c) min_turns met (CLIMAX_min = 3). Across all 4 runs, this condition fired in:
   - 2229: T10 (CLIMAX→RESOLUTION) — converged via hard cap (climax_turn_count=4) not early exit
   - 2159: T10 (CLIMAX→RESOLUTION) — converged via hard cap
   - 2258: T16 (CLIMAX→RESOLUTION) — converged via hard cap
   - 2247: T19 (CLIMAX→RESOLUTION) — converged via hard cap
   
   None of the early exits were triggered by the signal-gated path. All exits were via hard cap (climax_turn_count >= limit).

2. **Sanitizer downgrades are NOT preventing early exit — the issue is different.** The early exit requires a thread resolved on the *previous* turn. The curtain_call guidance (active at T1, forced at T+limit-1) instructs Record to resolve the main pressure thread during CLIMAX. But the sanitizer runs every 5 turns, which may or may not align with CLIMAX timing.

3. **Thread resolution rates are high (66-100%) but fast (avg 1.8-2.9 turns).** Threads are being resolved, not just downgraded. The sanitizer resolves threads via `resolved_threads` in some runs:
   - 2159 T25: `syndicate_asset_diversion` resolved
   - 2258 T10: `intelligence_leak` resolved
   - 2247 T25: `supply_manipulation` resolved
   
   But these are isolated events, not a pattern. Most sanitizer runs update without resolving.

4. **TTL-based culling (thread_memory_ttl = 3 turns) is NOT affecting early exit logic.** Completed threads persist beyond 3 turns in the prompt context — the TTL only affects what's shown to the LLM, not the engine's ability to detect `resolved_turn == turn_no - 1`.

5. **The hypothesis is partially wrong:** CLIMAX is NOT forced to rely solely on extension or hard cap because of sanitizer downgrades. It's forced because the early exit condition (thread resolved on previous turn + low convergence) is narrow. The convergence rarely drops below 1 during CLIMAX (it's typically 3-5), so even if a thread is resolved, the convergence gate prevents early exit.

**Meta improvements:**

- The early exit condition `total_convergence_score < config.convergence_exit_threshold` (default 1) is too strict. During CLIMAX, convergence is typically 3-5. Even if a thread is resolved, the convergence stays above 1 due to beat_streak and threat_thread components. Consider lowering `convergence_exit_threshold` to 0 or removing the convergence gate for early exit (rely solely on the thread-resolved signal).

- The curtain_call system (active at T1, forced at T+limit-1) should more strongly encourage thread resolution. The "forced" curtain_call already warns the LLM, but the Record extractor often ignores it in favor of updating progress. Consider making curtain_call a hard requirement in the Record prompt.

**Cross-cutting concerns:**

- The interaction between sanitizer timing and CLIMAX timing is a latent source of pacing inconsistency. If the sanitizer runs on a CLIMAX turn and resolves a thread, the early exit fires on the next turn. If it doesn't, the CLIMAX continues to hard cap. This creates an unpredictable CLIMAX length that depends on sanitizer luck, not narrative state.

---

## 1.4 Beat System as Convergence Wildcard

**Architecture docs to reference:**
- `docs/architecture/pacing-systems.md` — section 3 (GM beats, beat types, beat lifecycle), section 2 (convergence score)
- `docs/architecture/cross-module-contracts.md` — computation functions, beat constraint derivation

**Hypothesis:** Beats contribute to convergence independently of thread urgency. If the ruling/narration generates beats unevenly across runs, that could explain convergence differences between packs/personas independently of thread behavior.

**Data sources:**
- `ccya/engine/_pacing.py` — beat_streak calculation, BEAT_BUCKETS
- Events: `kind: "extract"` beat_component data
- `evals/runs/2026-07-17_0.32.1_2e3d0188/pacing.md` — existing beat_streak findings

**Investigation steps:**
1. How is beat_streak calculated? (see pacing-systems.md:53 for convergence components, BEAT_BUCKETS for tension bucket mapping)
2. Extract beat_component values from extract events across all 5 runs
3. Correlate beat patterns with convergence differences
4. Are beats being generated consistently, or is there persona/pack bias?
5. **Gap:** Check beat diversity ban — pacing-systems.md:126. World step enforces a 5-beat ban on types/NPCs/threads appearing 2+ times. Does this artificially suppress beat_streak by preventing repeat beat types?
6. **Gap:** Check `derive_allowed_beat_types()` — pacing-systems.md:392. Phase + directive determine allowed beat types. Does this phase-based filtering interact with beat_streak to suppress certain tension types?

**Findings:**

1. **Beat streak is the dominant convergence component.** Across all 4 runs, beat_streak = 1 on the majority of turns. The 2/4 threshold with carry-over makes it nearly impossible to stay at 0 for more than a couple turns. This means convergence is effectively determined by `1 (beat_streak) + threat_thread (0-1) + other components (mostly 0)`.

2. **Beat type distribution varies significantly by pack/persona:**
   - 2229 (golden-piracy): pressure(9), escalation(6), complication(4), revelation(3), callback(2), opportunity(1) — 6 types
   - 2159 (space-western): revelation(7), pressure(5), escalation(5), complication(4), breathing_room(1), opportunity(1), twist(1) — 7 types
   - 2258 (allied-ww2): escalation(9), complication(7), pressure(3), revelation(4), twist(1), breathing_room(1) — 6 types
   - 2247 (zombie-survival): pressure(11), complication(6), escalation(4), revelation(3), callback(1) — 5 types
   
   Golden-piracy shows the most beat type diversity. Zombie-survival is most pressure-heavy. This explains convergence differences between packs independently of thread behavior.

3. **Beat diversity ban (5-beat window) suppresses immediate repetition but NOT long-term recycling.** The same 2-3 threads dominate beat candidates across entire runs (65-84% of candidates). The `ruling_narration_and_npcs.md` deepdive confirms this pattern.

4. **Phase-based filtering in `derive_allowed_beat_types()` interacts with beat_streak:**
   - SETUP: All 8 types allowed (wide diversity)
   - RISING: 5 tension-focused types (pressure, complication, escalation, revelation, twist)
   - CLIMAX: 6 types (pressure, escalation, complication, revelation, callback, twist) — no opportunity/breathing_room
   - RESOLUTION: 3 respite types only (breathing_room, callback, revelation)
   - BREATHER: 4 types (opportunity, revelation, callback, breathing_room)
   
   This phase filtering suppresses respite beats during RISING/CLIMAX, which reinforces the tension bias in beat_streak.

5. **Beat_streak is too easy to trigger.** The 2/4 threshold with carry-over means beat_streak = 1 is the default state. This contributes to the narrow convergence distribution (0-3 typical). The beat system is doing most of the convergence work, not thread urgency.

**Meta improvements:**

- The beat_streak threshold (2/4 with carry-over) is too easy. Consider raising to 3/4 or removing carry-over to make beat_streak a more meaningful tension signal. This would increase the weight of thread urgency in convergence, making the urgent_thread component more impactful.

- The phase-based beat filtering suppresses respite types during RISING/CLIMAX, which creates a self-reinforcing tension loop. During RISING, only tension/discovery types are allowed, which makes beat_streak = 1 nearly guaranteed, which pushes convergence higher, which pushes toward CLIMAX. Consider allowing a small number of respite beats during RISING to add pacing variety.

**Cross-cutting concerns:**

- The beat system is the primary driver of convergence, not thread urgency as the design intends. The convergence formula weights urgent_thread at 0-2 points (highest individual component), but in practice beat_streak contributes 1 on most turns while urgent_thread contributes 0 on most turns. This inverts the intended weighting: thread urgency should be the primary convergence signal, but beats are doing the heavy lifting.

- The dampening loop (section 1.1) and beat dominance (section 1.4) interact: the sanitizer downgrades urgency, which reduces urgent_thread convergence, which makes beat_streak relatively more important, which reinforces the convergence pattern that the dampening loop is suppressing. This is a feedback loop that stabilizes pacing at a low-tension baseline.

---

## Summary of Cross-Cutting Concerns

1. **Dampening loop is real and impactful.** The sanitizer consistently downgrades urgency (0 escalations across all runs), which suppresses the highest-value convergence component (urgent_thread). This is the primary mechanism behind the narrow convergence distribution.

2. **Thread creation via thread_update is ungoverned.** The LLM creates threads by appearing in thread_update without thread_add. This is the dominant creation path and bypasses the thread_add gate (cooldown, cap eviction).

3. **Convergence formula vs. thread lifecycle contradiction.** The convergence formula weights urgent threads heavily (0-2 points), but the thread lifecycle (Record + Sanitizer) systematically removes urgency. The system should either: (a) make the sanitizer escalate as well as downgrade, or (b) reduce the weight of urgent_thread in convergence.

4. **Beat system is the de facto convergence driver.** Due to the dampening loop suppressing urgent_thread, beat_streak dominates convergence. This inverts the design intent where thread urgency should be the primary pacing signal.

5. **Early CLIMAX exit is constrained by convergence threshold, not by sanitizer.** The convergence_exit_threshold (default 1) is too high during CLIMAX where convergence is typically 3-5. Even resolved threads can't trigger early exit because beat_streak keeps convergence above 1.
