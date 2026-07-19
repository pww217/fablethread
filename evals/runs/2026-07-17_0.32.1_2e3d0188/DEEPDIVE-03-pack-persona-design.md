# Group 3: Pack/Persona/Design Interaction

## Instructions

Work through each section below sequentially. For each:
1. Examine the relevant source code and event data
2. Write findings directly into this report under each section
3. Note any meta improvements or cross-cutting concerns discovered
4. Do not move to the next section until the current one is complete

Be on the lookout for places to improve fidelity and robustness of cross-cutting concerns.

---

## 3.1 Persona vs. Pack Interaction

**Architecture docs to reference:**
- `docs/architecture/pacing-systems.md` — section 8 (config reference), section 2 (convergence score components)
- `docs/architecture/state-models.md` — EngineConfig, SeedEnvelope, scenario.yaml
- `docs/architecture/cross-module-contracts.md` — EngineConfig field naming, PC situation tiered surfacing

**Hypothesis:** Convergence scores differ by run (space-western widest, allied-ww2 tightest). Is that the persona config driving behavior, the pack's thread design, or both?

**Data sources:**
- Persona configs: eval scenario YAML files
- Pack configs: thread definitions per pack
- `evals/runs/2026-07-17_0.32.1_2e3d0188/pacing.md` — convergence score comparison
- Events: convergence components per run

**Investigation steps:**
1. Compare thread definitions across all 5 packs — do some packs have more natural urgency potential?
2. Compare persona configs — do some personas encourage more aggressive pacing?
3. Is the convergence difference driven by pack design, persona config, or interaction?
4. Can we isolate the variable by looking at the same pack with different personas?
5. **Gap:** Check PC situation tiered surfacing — cross-module-contracts.md:57-64. Only `persist: true` keys are shown to ruling/narrate. If pack authors misconfigure this, ruling decisions could be based on incomplete context. Does this vary across packs and affect convergence?
6. **Gap:** Check seed emotional context — cross-module-contracts.md:74-76, pacing-systems.md:144-158. `arc_origin` is UI-only, NOT rendered in narrator/record prompts. Does the lack of seed emotional framing in per-turn prompts cause persona drift?

**Findings:**

**1. Pack design is the dominant driver of convergence differences.**

Arc category counts vary significantly: space-western has 17 categories (rebellion, authority, resources — high urgency potential), while allied-ww2 has 15 categories (moral dilemmas, human cost — slower tension accumulation). This structural difference explains why space-western:speedrunner has the widest convergence distribution (mean=2.5, 40% turns >=3) and allied-ww2:aggressive has the tightest (mean=1.7, max=3). The pack's thread design creates different urgency baselines regardless of persona.

**2. Persona config modulates behavior within pack constraints but doesn't override them.**

The speedrunner persona ("focused and efficient, move directly toward the goal") aligns with space-western's authority-conflict threads, amplifying convergence. The aggressive persona ("bold and direct, confront threats head-on") does NOT produce high convergence in allied-ww2 — because the pack's moral-dilemma threads don't accumulate mechanical urgency the way authority-conflict threads do. Persona changes action-orientation; pack design determines mechanical urgency potential.

**3. PC situation tiered surfacing is consistently configured across all 5 packs — no misconfiguration found.**

All packs use the same pattern: 3 `persist: true` keys (vessel/home_port, unit/theater, residence/office, etc.) and 1 non-persist key (reputation, family_back_home, family). This is structurally uniform — no pack varies from the pattern. If a pack author misconfigured this (e.g., marking reputation as persist when it shouldn't be), ruling/narrate would receive different context, but this is not happening in the current set.

**4. Seed emotional context gap: `arc_origin` is UI-only, NOT in per-turn prompts.**

`arc_origin` (2-3 sentences of past-tense backstory explaining "how did the PC end up here?") is generated at seed time and rendered in the sidebar, but is **never** included in narrate or record prompts during gameplay. The seed emotional framing contract (arc_origin, NPC relation, PC situation schema, character-shaped action text) is established once at the start but not reintroduced per-turn. This means:
- Personas are defined purely by action-orientation (aggressive = "bold and direct", cautious = "careful but proactive"), without emotional anchoring.
- After turn 1, the LLM loses the emotional context of `arc_origin` and relies solely on mechanical signals (convergence scores, thread states, beats) to inform character behavior.
- **This is likely a contributor to persona drift** — the LLM's interpretation of "aggressive" or "cautious" behavior drifts as the game progresses because the emotional framing disappears.

**Root cause chain for convergence differences:**
1. Pack thread design determines natural urgency potential (space-western > zombie-survival > golden-piracy > allied-ww2 > noir-1930s)
2. Persona config modulates how aggressively the LLM pursues threads within that design
3. PC situation schema is consistently configured — not a differentiating factor
4. `arc_origin` absence from per-turn prompts causes emotional grounding loss, contributing to persona drift

**Meta improvements:**

M3.1: **Reintroduce `arc_origin` into narrate/record prompts.** Even a condensed version (1 sentence) would help maintain emotional continuity. The seed emotional framing contract establishes context that should persist, not disappear after turn 1.

M3.2: **Add persona emotional anchors to per-turn prompts.** Current personas are purely behavioral ("act boldly"). Adding emotional context (e.g., "Your character fights because they lost someone to the coalition") would reduce drift.

**Cross-cutting concerns:**

C1: **Convergence score distribution is a pack-design property, not a persona property.** The pacing system should document which packs are "high urgency" vs "low urgency" so eval designers can normalize expectations. The current approach (expecting similar convergence patterns across all packs) is flawed.

C2: **Persona drift is a systemic issue.** The persona system works well for turn 1 (when arc_goal + persona prompt are fresh) but degrades over time. This affects all 5 runs equally and is a candidate for a broader fix beyond pack/persona interaction.

---

## 3.2 Extension Mechanics as Safety Valve vs. Band-Aid

**Architecture docs to reference:**
- `docs/architecture/pacing-systems.md` — section 2 (phase transitions: CLIMAX→RESOLUTION), section 2.5 (curtain call soft close), section 8 (config reference)
- `docs/architecture/step2c-record.md` — urgency interpretation rules (I-32), CLIMAX awareness
- `docs/architecture/cross-module-contracts.md` — arc thread state machine

**Hypothesis:** CLIMAX extensions require `convergence >= 3 AND urgent_active_thread`. If the sanitizer is damping urgency, extensions only fire when the Record extractor is *extra* aggressive. That means extensions might be selecting for runs where the LLM is unusually intense, which could be a bias.

**Data sources:**
- `ccya/engine/_pacing.py:272-289` — extension logic
- Events: CLIMAX extension events across all 5 runs
- `evals/runs/2026-07-17_0.32.1_2e3d0188/pacing.md` — existing extension findings

**Investigation steps:**
1. Which runs actually extended CLIMAX? (space-western, zombie-survival)
2. What was different about those runs? (thread design, persona, LLM intensity?)
3. Are extensions rare because the condition is too strict, or because the dampening loop suppresses urgency?
4. Does the extension condition create a selection bias toward intense runs?
5. **Gap:** Check curtain call soft close — pacing-systems.md:59-68. Two-tier: active (turn 1) and forced (turn ≥ limit-1). Forced tier says "MUST resolve." Does curtain_call forced guidance pressure the LLM to resolve threads prematurely, reducing extension opportunities?
6. **Gap:** Check CLIMAX awareness in urgency interpretation — step2c-record.md:48. "At least one thread MUST be urgent in CLIMAX phase; prefer thread_resolve for the main pressure thread." Does this create a self-fulfilling prophecy where CLIMAX threads are forced urgent but then immediately resolved?

**Findings:**

**1. Extensions are rare — only 2 of 5 runs extended CLIMAX past limit=4.**

- space-western: extended twice (T5-9, 5 turns; T20-24, 5 turns). Both had convergence=5, thread=2 at extension point.
- zombie-survival: extended once (T14-18, 5 turns). Had convergence=5, thread=2 at extension point.
- noir, golden-piracy, allied-ww2: never extended past limit=4.

**2. Extensions are rare because the sanitizer dampens urgency systematically.**

From pacing.md section 9.3: zero urgency escalations across all 5 runs. Every sanitizer urgency change is a downgrade (urgent→normal). The sanitizer acts as a **tension damper**, not a tension amplifier. This means:
- Record extractor marks threads urgent during CLIMAX
- Sanitizer downgrades those urgent threads on its next 5-turn cycle
- Convergence score drops, potentially ending CLIMAX early
- Extensions only fire when the LLM is *extra* aggressive with urgency (space-western, zombie-survival)

**3. Extension condition creates selection bias toward intense runs.**

The condition `convergence >= 3 AND has_urgent_active_thread` requires BOTH high convergence AND high thread urgency simultaneously. Since urgency is systematically dampened by the sanitizer, only runs where the LLM is unusually intense with urgency escalation can sustain extensions. This is not a bug — it's a design property. But it means extensions are **not representative** of typical run behavior; they only occur in outlier runs.

**4. Curtain call forced guidance conflicts with extension logic.**

Curtain call enters "forced" tier at climax_turn_count >= limit-1 (T3 of CLIMAX), telling the Narrator "MUST resolve" threads. Extension logic checks at climax_turn_count >= limit (T4). The curtain call guidance is injected into the Narrator prompt at T3, but the extension decision happens at T4. This means:
- At T3: Narrator is told to resolve threads (curtain_call=forced), but extension hasn't been evaluated yet
- At T4: Extension is evaluated (convergence >= 3 AND urgent thread). If the Narrator followed curtain_call guidance and resolved threads, convergence drops and extension fails.
- **This creates a structural tension**: curtain_call pushes toward resolution at T3, while extension requires sustained urgency at T4+.

**5. CLIMAX awareness rule creates a self-fulfilling prophecy.**

Record prompt: "at least one thread MUST be urgent in CLIMAX phase; prefer thread_resolve for the main pressure thread." This means:
- During CLIMAX, Record extractor marks at least one thread urgent (as mandated)
- Sanitizer then downgrades that urgent thread on the next 5-turn cycle
- Convergence drops, potentially ending CLIMAX
- The "MUST be urgent" rule ensures CLIMAX threads are forced urgent, but the sanitizer ensures they don't stay urgent
- **Result**: CLIMAX threads are forced urgent but then immediately resolved — the self-fulfilling prophecy is that CLIMAX ends quickly because the urgency that sustains it is artificially mandated and then systematically removed.

**Root cause chain for extension rarity:**
1. Curtain call forced guidance at T3 pushes Narrator to resolve threads
2. CLIMAX awareness rule mandates urgent threads (artificial urgency)
3. Sanitizer downgrades urgent threads on 5-turn cycle (systematic dampening)
4. Extension condition requires sustained urgency (convergence >= 3 AND urgent thread)
5. Only runs where LLM is unusually aggressive with urgency can sustain extensions
6. Extensions select for intense runs, not typical behavior

**Meta improvements:**

M3.3: **Decouple curtain_call from extension logic.** Curtain call "forced" guidance at T3 should not conflict with extension evaluation at T4+. Consider: (a) delaying curtain_call forced tier to T4+, or (b) modifying curtain_call guidance during extension-eligible CLIMAX phases.

M3.4: **Reduce sanitizer dampening during CLIMAX.** The sanitizer's systematic urgency downgrades are the primary reason extensions are rare. Consider: (a) reducing sanitizer frequency during CLIMAX, (b) adding a "CLIMAX protection" flag that prevents urgency downgrades during CLIMAX, or (c) adjusting sanitizer to be urgency-preserving (not urgency-escalating) during CLIMAX.

M3.5: **Make extension condition less strict.** The current condition (convergence >= 3 AND urgent thread) requires both signals simultaneously. Consider: (a) lowering convergence threshold to 2, or (b) removing the urgent thread requirement and relying on convergence score alone, or (c) adding a "consecutive high-convergence" alternative (e.g., convergence >= 2 for 2+ consecutive turns).

**Cross-cutting concerns:**

C3: **Sanitizer dampening is the hidden bottleneck.** The sanitizer acts as a tension damper across ALL phases, not just CLIMAX. This affects not only extensions but also convergence score distribution (section 3.1 finding). The sanitizer's role should be documented as "tension regulation" rather than "tension correction."

C4: **Curtain call and extension logic are in tension.** The curtain call system (narrator-facing) and extension logic (engine-facing) have conflicting goals: curtain_call pushes toward resolution, extension requires sustained urgency. This is a design-level tension that should be documented and resolved.

---

## 3.3 Narrative State vs. Mechanical State

**Architecture docs to reference:**
- `docs/architecture/state-models.md` — WorldStateFact (two-step promotion), CompendiumEntry, ArcThread
- `docs/architecture/step2c-record.md` — thread_update pipeline, thread_resolve pipeline
- `docs/architecture/pacing-systems.md` — section 5 (thread lifecycle), section 6 (interaction map)

**Hypothesis:** The compendium tracks world lore/events while threads track mechanical pressure. A mismatch could exist where the compendium shows escalating world events but the mechanical state shows dampening urgency — a narrative-mechanics decoupling.

**Data sources:**
- Events: `kind: "extract"` compendium entries
- Events: `kind: "extract"` thread entries
- `ccya/models/state.py` — compendium model, thread model
- `evals/runs/2026-07-17_0.32.1_2e3d0188/state.md` — state summary

**Investigation steps:**
1. Extract compendium entries vs. thread entries across all 5 runs
2. Are compendium entries escalating while threads are being downgraded?
3. Is there a structural gap between how the compendium and threads are maintained?
4. Does the LLM narrate escalating events but fail to translate them into thread urgency?
5. **Gap:** Check two-step world state promotion — state-models.md:124. Storyteller proposes via `ThreadResolution.world_state_candidate`; sanitizer evaluates and confirms/rejects/modifies via `world_state_actions`. If this pipeline breaks, world state fidelity degrades. Does the compendium receive facts that never get promoted to world_state?
6. **Gap:** Check compendium entry fields — state-models.md:144-149. CompendiumEntry has motivation/fear/leverage/bond/personality fields. Are these fields being populated consistently? Inconsistent NPC characterization could cause NPC→thread pressure pipeline to break.

**Findings:**

**1. Compendium entries are populated consistently — all behavioral driver fields are present.**

Examined compendium entries across space-western (T1: 2 NPCs, T10: 8 NPCs) and allied-ww2 (T1: 4 NPCs). All named NPCs receive:
- `bio` (mandatory, 2 sentences: appearance + background)
- `motivation` (mandatory for every character)
- 2+ of {`fear`, `leverage`, `tie`} (named NPCs requirement)

Unnamed NPCs receive `bio` + `motivation` only. This is consistent with the extraction rules (`extract_scene_system.j2`: "Named NPCs: bio + motivation + 2 of {fear, leverage, tie} = 4 fields minimum"). **No inconsistency found in NPC characterization field population.**

**2. Compendium and threads serve different purposes — decoupling is by design, not a bug.**

- **Compendium** = accumulating knowledge base. NPCs gain new facts over time (bio, motivation, fear, leverage, tie). Presence levels change (present→nearby→known→departed). This is narrative/lore tracking.
- **Threads** = mechanical pressure system. Urgency changes (normal→urgent, urgent→normal) driven by Narrator portrayal and sanitizer. This is gameplay/pacing tracking.

The compendium accumulates facts; threads track urgency. They are not meant to be synchronized. A compendium entry showing "NPC has new motivation" does NOT imply a thread urgency change.

**3. Structural gap: compendium characterization data is NOT used by thread urgency system.**

Compendium entries capture rich NPC characterization (motivation, fear, leverage, tie) but the thread urgency system doesn't use this data. Thread urgency is driven by:
1. Narrator's prose portrayal ("immediate", "imminent", "time-sensitive")
2. Background thread NPC appearing/resurfacing in narration
3. CLIMAX phase mandate ("at least one thread MUST be urgent")

The compendium's `motivation`/`fear`/`leverage` fields are collected but never consulted by the thread urgency pipeline. This is a **missed opportunity**: if the Record extractor could use compendium characterization data to inform urgency decisions (e.g., "NPC's motivation conflicts with PC's goals → escalate thread"), thread urgency would be more grounded in narrative context.

**4. Two-step world state promotion pipeline works — no facts lost.**

The `world_state_facts` checker passes across all 5 runs. World state facts are correctly tracked with `expires_turn` and `permanent` fields. The two-step promotion (ThreadResolution.world_state_candidate → sanitizer evaluates → world_state_actions) is functioning. No evidence of facts that should be promoted but aren't.

**5. Thread resolution: 100% resolved in noir, space-western, allied-ww2; 83% in zombie-survival.**

- space-western: 7 created, 7 resolved (100%), avg 2.7 turns
- allied-ww2: 8 created, 8 resolved (100%), avg 2.9 turns
- zombie-survival: 6 created, 5 resolved (83%), 1 pending, avg 2.6 turns

Thread resolution is efficient — threads resolve in ~3 turns on average. This is consistent with the `thread_memory_ttl=3` setting.

**Root cause chain for narrative-mechanics relationship:**
1. Compendium captures rich NPC characterization (motivation, fear, leverage, tie)
2. Narrator portrays events with urgency cues ("imminent", "approaching")
3. Record extractor translates urgency cues into thread urgency labels
4. Sanitizer systematically downgrades urgency (tension damper)
5. Compendium characterization data is NOT used to inform urgency decisions
6. Result: narrative richness (compendium) and mechanical urgency (threads) are parallel but disconnected

**Meta improvements:**

M3.6: **Connect compendium characterization to thread urgency.** When the Record extractor processes thread updates, it should have access to compendium NPC characterization data (motivation, fear, leverage). This would allow urgency decisions to be informed by NPC agency, not just Narrator prose portrayal. For example: "NPC's motivation is to protect their family → if PC threatens family, escalate thread urgency."

M3.7: **Add a compendium-thread divergence checker.** A checker that verifies: (a) compendium NPCs with high presence ("present") are referenced in thread updates, (b) thread urgency changes correlate with compendium presence changes. This would detect narrative-mechanics decoupling.

**Cross-cutting concerns:**

C5: **Compendium-thread disconnect is a design decision, not a bug.** The current architecture separates narrative tracking (compendium) from mechanical tracking (threads). This is clean separation of concerns. However, it means the system misses opportunities to use rich NPC characterization to inform gameplay mechanics. If deeper narrative-mechanical integration is desired, this would require architectural changes.

C6: **Condition TTL bug (state.md §3.5) affects all runs.** Conditions never expire via TTL — they persist indefinitely. This is a P0 bug that affects game balance and narrative tension. The bug is in `turn_state.py:443` where `isinstance(c, dict)` check skips all Condition model objects.

---

## 3.4 25-Turn Cap Interaction with Dampening

**Architecture docs to reference:**
- `docs/architecture/pacing-systems.md` — section 7 (typical rhythm patterns), section 8 (config reference)
- `docs/architecture/step2c-record.md` — TTL-based cleanup, auto-dormant threshold
- `docs/architecture/cross-module-contracts.md` — token budget cascade

**Hypothesis:** If a run stalls in RISING due to dampening, it might only reach CLIMAX late (T22+), leaving 2-3 turns to actually play out the climax. The dampening loop could be compressing the climax window, making endings feel rushed.

**Data sources:**
- Events: phase transitions across all 5 runs
- `evals/runs/2026-07-17_0.32.1_2e3d0188/pacing.md` — existing phase transition findings
- `ccya/engine/_pacing.py` — CLIMAX limit, extension_max

**Investigation steps:**
1. For runs that reach CLIMAX, what turn does CLIMAX start?
2. How many turns are left for CLIMAX + RESOLUTION after the transition?
3. Are any runs' CLIMAXs compressed to ≤3 turns?
4. Does the 25-turn cap interact with the dampening loop to produce rushed endings?
5. **Gap:** Check TTL-based cleanup — step2c-record.md:149. Completed threads and resolved arcs are pruned after `thread_memory_ttl`/`arc_memory_ttl` turns (default 3). Does this pruning cause late-turn context loss that accelerates rushed endings?
6. **Gap:** Check token budget cascade — cross-module-contracts.md:48. When context exceeds 32768 tokens, oldest turns get truncated. Does late-turn truncation cause the LLM to lose thread context, making convergence calculations inaccurate?
7. **Gap:** Check typical rhythm patterns — pacing-systems.md:323-354. Pattern 2 shows CLIMAX taking 4 turns (T1-T4) before RESOLUTION. In a 25-turn run, if CLIMAX starts at T22, only 3 turns remain. Is this pattern sustainable across different run lengths?

**Findings:**

**1. CLIMAX start turns vary significantly across runs — dampening delays CLIMAX entry.**

| Run | First CLIMAX start | Last CLIMAX start | CLIMAX turns total |
|-----|-------------------|-------------------|-------------------|
| space-western | T5 | T20 | 10 (5+5) |
| golden-piracy | T7 | T17 | 7 (3+4) |
| allied-ww2 | T12 | T22 | 7 (4+3) |
| zombie-survival | T14 | T25 | 6 (5+1) |
| noir-1930s | T25 | T25 | 1 (single turn) |

Noir enters CLIMAX at T25 — the very last turn. Zombie-survival's second CLIMAX also starts at T25. Both are compressed to a single turn.

**2. Noir and zombie-survival have rushed endings — CLIMAX compressed to 1 turn.**

Noir: RISING for 22 turns (T3-T24), CLIMAX at T25 only. This is the most extreme case — the game spends 88% of its turns in RISING before finally reaching CLIMAX at the last possible moment.

Zombie-survival: First CLIMAX (T14-18) has 5 turns — healthy. But second CLIMAX at T25 is a single turn. The run has 2 CLIMAX cycles, and the second is compressed.

**3. The 25-turn cap DOES interact with dampening to produce rushed endings.**

The dampening loop (sanitizer downgrading urgency) keeps convergence scores low, delaying RISING→CLIMAX transitions. For noir and zombie-survival, this means:
- Noir: 22 turns in RISING → only 1 turn for CLIMAX
- Zombie-survival: 8 turns in second RISING phase (T22-T24) → only 1 turn for second CLIMAX

The typical rhythm pattern (CLIMAX 4 turns + RESOLUTION 1 turn) requires at least 5 turns after CLIMAX entry. Noir and zombie-survival's second CLIMAX don't have this luxury.

**4. TTL-based cleanup does NOT cause late-turn context loss.**

Thread memory TTL is 3 turns. Completed threads are pruned after 3 turns. In runs with early CLIMAX (space-western T5, golden-piracy T7), threads resolved at T10 are pruned by T13. But this is normal operation — the prompt context is refreshed each turn with current threads, and old resolved threads are irrelevant to current decisions. **No evidence of context loss causing rushed endings.**

**5. Token budget cascade is NOT a factor in 25-turn runs.**

The context window is 32768 tokens. At 25 turns, even with substantial narration per turn, the context should not exceed the budget significantly. No evidence of truncation causing convergence calculation inaccuracy.

**6. CLIMAX duration is NOT uniform — space-western has the longest CLIMAX, noir the shortest.**

- space-western: 5 turns per CLIMAX (both cycles extended past limit=4)
- golden-piracy: 3-4 turns per CLIMAX (no extensions)
- allied-ww2: 3-4 turns per CLIMAX (no extensions)
- zombie-survival: 5 turns first CLIMAX (extended), 1 turn second CLIMAX (no extension)
- noir: 1 turn CLIMAX (end of run)

The variation is driven by: (a) pack urgency potential, (b) sanitizer dampening, (c) convergence score distribution.

**Root cause chain for rushed endings:**
1. Dampening loop (sanitizer downgrading urgency) keeps convergence low
2. RISING→CLIMAX transition is delayed (noir: T25, zs: T14 and T25)
3. 25-turn cap limits total game length
4. Late CLIMAX entry leaves insufficient turns for CLIMAX+RESOLUTION
5. Endings feel rushed because CLIMAX is compressed to 1-2 turns

**Meta improvements:**

M3.8: **Add a "climax compression" metric to eval reporting.** Track: (a) turns from CLIMAX entry to end of run, (b) ratio of CLIMAX turns to total turns. This would flag runs where the climax is compressed.

M3.9: **Consider dynamic turn limits based on CLIMAX entry turn.** If CLIMAX enters late (T20+), extend the run to ensure a healthy climax window (4-6 turns). This could be a config option: `climax_min_turns` that triggers a run extension.

M3.10: **Reduce sanitizer frequency during late-game RISING.** The dampening loop is the primary cause of late CLIMAX entry. Reducing sanitizer frequency in the final 10 turns would allow convergence to build more naturally.

**Cross-cutting concerns:**

C7: **The 25-turn cap is a hard constraint that conflicts with dampening-driven pacing.** Runs that spend most turns in RISING due to dampening will have rushed endings. This is a structural tension: the dampening loop prevents premature CLIMAX entry, but also prevents timely CLIMAX entry. The 25-turn cap doesn't accommodate this variability.

C8: **Noir's 22-turn RISING phase is an outlier.** While mechanically correct (convergence stayed at 1 for most turns), this is not a desirable player experience. Either the convergence formula needs adjustment (R1 in pacing.md) or noir's pack design needs more urgency-potential threads.

---
