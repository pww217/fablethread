# Eval Report — `full_cycle`

**Pack:** `eval-pack` · **Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8` · **Temp override:** `None`  
**Started:** 2026-05-11T04:03:53.967398+00:00 · **Finished:** 2026-05-11T04:11:43.610784+00:00  
**Output dir:** `/Users/pwilson/Repos/ccya/evals/runs/20260511T040353Z_n8vfdtpv`  
**Compared against:** _(no prior run found)_

## Judge Summary

**Mechanical:** 2/5  
**Narrative:** 3/5  
**System Cohesion:** 2/5  
**Prompt Quality:** 2/5  
**Compaction:** 1/5  
**State Fidelity:** 69.0%  
**Prompt Adherence:** 63.0%
**Rubric:** `/Users/pwilson/Repos/ccya/evals/rubrics/default.md`
**Judge model:** `mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit`

**Pipeline scores:**
- rules: 3/5
- narrate: 2/5
- extract_scene: 3/5
- extract_state: 3/5
- extract_progress: 2/5

**Trace:** [`full_cycle.trace.md`](full_cycle.trace.md)
**Judge response:** [`full_cycle.judge.md`](full_cycle.judge.md)

## ⚠️  Flagged

### `rejected_deltas` — 1 rejected delta(s) across the run

- turn 13: 1 rejected


## Judge Verdict (full)

# SECTION 1 — Mechanic Lifecycle Tables

### 1A — Momentum Table

| Turn | Roll Band | Δ Momentum | Band Before→After | Tone Match? | Flag |
|------|-----------|------------|-------------------|-------------|------|
| 1 | partial | 0 | 0→0 | Yes | — |
| 2 | none | 0 | 0→0 | Yes | — |
| 3 | crit_fail | -2 | 0→-2 | Yes | — |
| 4 | none | 0 | -2→-2 | Yes | — |
| 5 | setback | -1 | -2→-3 | Yes | — |
| 6 | partial | 0 | -3→-3 | Yes | — |
| 7 | fail | 0 | -3→-3 | Yes | — |
| 8 | fail | 0 | -3→-3 | Yes | — |
| 9 | fail | 0 | -3→-3 | Yes | — |
| 10 | setback | 0 | -3→-3 | Yes | — |
| 11 | fail | 0 | -3→-3 | Yes | — |
| 12 | partial | 0 | -3→-3 | Yes | — |
| 13 | none | 0 | -3→-3 | Yes | — |

**Assessment:** Momentum deadlocks at `-3` from Turn 5 through Turn 13. The engine fails to generate any positive delta or recovery band, creating a mechanical death spiral. The tone matches the low momentum, but the lack of variance breaks the feedback loop.

### 1B — GM Beat Table

| Generated (Tn) | Beat Type | Surfaced (Tm) | Surface Lag (turns) | Effect | Flag |
|----------------|-----------|---------------|---------------------|--------|------|
| T3 | complication | T4 | 1 | Halden agitated, cart spooks | — |
| T4 | complication | T5 | 1 | Cart driver spooks | — |
| T5 | pressure | T6 | 1 | Toughs close distance | — |
| T6 | escalation | T7 | 1 | Toughs drag player | — |
| T7 | pressure | T8 | 1 | Edda draws eyes | — |
| T8 | escalation | T9 | 1 | Scarred Tough blocks path | — |
| T9 | pressure | T10 | 1 | Bald Tough drags player | — |
| T10 | escalation | T11 | 1 | Toughs drag player | — |
| T11 | pressure | T12 | 1 | Bald Tough lunges | — |
| T12 | pressure | T13 | 1 | Bald Tough charges | — |
| T13 | pressure | T14 | 1 | Bald Tough scans barrels | — |

**Assessment:** Beats generate every turn with 0-1 turn lag, but they are overwhelmingly `pressure`/`escalation`/`complication`. The beat directive consistently overrides player input (T7, T10), breaking the narrative loop. No `breathing_room` or `opportunity` beats appear.

### 1C — Scene Pressure Table

| ID | Added (Tn) | Urgency | Escalated? | Resolved (Tm) | Lifespan (turns) | Flag |
|----|------------|---------|------------|---------------|-----------------|------|
| halden_distrust | 3 | immediate | No | End | 10 | OVERLONG |
| inn_entrance_blockade | 5 | immediate | No | 9 | 4 | — |
| failed_bribe_consequence | 6 | immediate | No | 7 | 1 | — |
| inn_witness_pressure | 7 | building | No | 12 | 5 | — |
| thug_escalation | 8 | immediate | No | 11 | 3 | — |
| forced_abduction | 9 | immediate | No | 12 | 3 | — |
| bald_tough_retaliation | 11 | immediate | No | 13 | 2 | — |

**Assessment:** `halden_distrust` sits inert for 10 turns with no narrative callback or resolution, acting as mechanical dead weight. Other pressures cycle appropriately but never escalate stakes mechanically; they only change flavor text.

### 1D — Condition Lifecycle Table

| ID | Added (Tn) | Source | Still Present (Tm) | Resolved | Duration (turns) | Flag |
|----|------------|--------|--------------------|----------|-----------------|------|
| bruised_ribs | 0 (seed) | engine | 13 | No | 13 | OVERLONG, IRRELEVANT |
| low_morale | 0 (seed) | engine | 2 | Yes | 2 | — |
| shaken | 7 | state | 8 | Yes | 1 | — |
| strained_ribs | 8 | state | 13 | No | 5 | OVERLONG, IRRELEVANT |
| exhausted | 10 | state | 11 | Yes | 1 | — |
| dizzy | 11 | state | 12 | Yes | 1 | — |

**Assessment:** `bruised_ribs` and `strained_ribs` persist for 5-13 turns with zero mechanical modifiers applied to rolls and zero narrative callbacks referencing the pain. They are purely mechanical noise.

### 1E — Quest Arc Table

| Quest ID | Created (Tn) | Objectives | Objectives Done | Resolved (Tm) | Outcome | Flag |
|----------|--------------|------------|-----------------|---------------|---------|------|
| settle_the_debt | 0 | 2 | 2 | 2 | completed | — |
| deliver_the_ledger | 0 | 3 | 1 | End | stalled | INCOMPLETE_CLOSE |
| clear_the_road_toughs | 0 | 2 | 1 | End | stalled | INCOMPLETE_CLOSE |

**Assessment:** `settle_the_debt` resolves cleanly. The other two quests stall after one objective is completed. Objectives 2 and 3 for both quests are never advanced, and the engine never generates new objectives or fails the quests, leaving the player in a static loop.

### 1F — Inventory Evolution Table

| Turn | Action | Item | Qty | Narration Reflected? | Extracted? | Flag |
|------|--------|------|-----|---------------------|------------|------|
| 2 | remove | credits | 500 | Yes | Yes | — |
| 11 | add | leather_pouch | 1 | Yes | Yes | — |
| 13 | remove | leather_pouch | 3 | Yes | Yes | AMOUNT_MISMATCH |

**Assessment:** `leather_pouch` extraction at T13 requests `amount: 3` but the stack only contains 1. The state extractor fails to validate against current stack before emitting, relying on the Python validator to clamp it. This is a prompt adherence failure.

---

# SECTION 2 — State Fidelity

### 2A — State Coherence
State evolves logically turn-over-turn. Inventory and conditions track correctly except for the T13 overdraw. Quest objectives advance when narrated, but the progress extractor repeatedly emits `done: false` for already-false objectives (T4, T6, T7, T9, T12, T13), polluting the state with redundant updates. Conditions accumulate without mechanical effect, creating a disconnect between state and rules.

### 2B — State Drift
- **Extraction drift:** Progress extractor emits `quest_updates: [{index: 2, done: false}]` for `deliver_the_ledger` and `clear_the_road_toughs` across 6 turns. This adds no state change but bloats the delta.
- **Narration drift:** Narration at T7 and T10 completely ignores player input, instead following the GM beat. State reflects the narrator's override, not the player's action, creating a fiction-state mismatch.

### 2C — State Completeness
- **Conditions:** `bruised_ribs` and `strained_ribs` never feed into `rules_outcome.cond_mod` or appear in narration. The state extractor and rules pipeline are decoupled.
- **Pressures:** `halden_distrust` persists for 10 turns without being consumed or resolved by the progress extractor.

### 2D — State Fidelity Rate Calculation
Turns with no rejected deltas AND no detected drift: T1, T3, T4, T5, T6, T8, T9, T11, T12. (9 turns)
Total turns: 13
Rate: 9 / 13 = 0.692 → **0.69**

---

# SECTION 3 — Prompt Quality Audit

### 3A — Rules Pipeline Prompt Audit
| Criterion | Score | Evidence (turn + quote) |
|-----------|-------|-------------------------|
| P1 | Y | System/static, user/turn-variable. |
| P2 | Y | Matches architecture diagram. |
| P3 | Y | No cross-pipeline redundancy. |
| P4 | Y | Schema and guidance separated. |
| P5 | Y | Clear decision rules. |
| P6 | Y | Concise. |
| P7 | Y | Priority numbered, JSON schema concrete. |
| P8 | FAIL | `rules_outcome` binding block never fed to narrator (T1-T12). Auto-checker `universal.narrate.binding_present` fires every rolled turn. |
| P9 | PARTIAL | Needs example for handling GM beat overrides vs player input. |

**Remediation summary:**
- **Missing data flow:** The rules pipeline emits `rules_outcome` but the engine fails to inject it into the Narrate user prompt. Fix: Update `run_turn()` to pass `rules_outcome` to Step 1.
- **Intent vs Beat conflict:** Rules prompt lacks guidance on how the narrator should prioritize player input over `pending_gm_beat`. Fix: Add explicit priority rule: "Player input dictates action; GM beat dictates flavor/consequence only."

### 3B — Narrate Pipeline Prompt Audit
| Criterion | Score | Evidence (turn + quote) |
|-----------|-------|-------------------------|
| P1 | Y | System/static, user/turn-variable. |
| P2 | Y | Rich inputs justified for prose. |
| P3 | Y | Narration fed to extractors is by design. |
| P4 | Y | Schema/guidance separated. |
| P5 | Y | Clear directives. |
| P6 | Y | Concise. |
| P7 | Y | Well-formatted. |
| P8 | FAIL | Ignores player input at T7 and T10 to follow GM beat. Violates "Player input is truth" rule. |
| P9 | PARTIAL | Needs few-shot for balancing GM beat integration vs player agency. |

**Remediation summary:**
- **Player intent override:** Narrator consistently ignores input when `pending_gm_beat` is present. Fix: Add prompt rule: "Integrate GM beat instruction as environmental pressure or NPC reaction, NEVER as a replacement for the player's stated action."
- **Missing rules binding:** Narrator receives no `rules_outcome` directive, breaking the dice-band binding loop. Fix: Inject `rules_outcome` into narrate prompt.

### 3C — Extract Scene Prompt Audit
| Criterion | Score | Evidence (turn + quote) |
|-----------|-------|-------------------------|
| P1 | Y | System/static, user/turn-variable. |
| P2 | Y | Matches architecture. |
| P3 | Y | No redundancy. |
| P4 | Y | Schema/guidance separated. |
| P5 | Y | Clear rules. |
| P6 | Y | Concise. |
| P7 | Y | Well-formatted. |
| P8 | FAIL | Adds `inn_patrons` (T10) and `shadowy_figure` (T9, T11) without grounding in narration or compendium. Violates "NPC Grounding Rule". |
| P9 | PARTIAL | Needs explicit grounding examples for ambient/observer NPCs. |

**Remediation summary:**
- **Ungrounded NPC addition:** Scene extractor invents `inn_patrons` and `shadowy_figure` when narration only implies background presence. Fix: Strengthen "NPC Grounding Rule" to require explicit narration mention or compendium ID match before `npc_add`.
- **Ambient filtering:** Prompt allows ambient crowd additions when named NPCs are present. Fix: Add hard cap: "Do not emit `npc_add` for ambient presence if ≥1 named NPC is already in `present_npcs`."

### 3D — Extract State Prompt Audit
| Criterion | Score | Evidence (turn + quote) |
|-----------|-------|-------------------------|
| P1 | Y | System/static, user/turn-variable. |
| P2 | Y | Matches architecture. |
| P3 | Y | No redundancy. |
| P4 | Y | Schema/guidance separated. |
| P5 | Y | Clear rules. |
| P6 | Y | Concise. |
| P7 | Y | Well-formatted. |
| P8 | FAIL | Emits `inventory_remove: {amount: 3}` for `leather_pouch` at T13 when stack is 1. Violates "Read current stack" rule. |
| P9 | PARTIAL | Needs explicit "do not emit if amount > current stack" rule. |

**Remediation summary:**
- **Overdraw emission:** State extractor emits amounts exceeding current inventory stack. Fix: Add hard prompt rule: "If requested remove amount > current stack amount, emit `amount: null` (full remove) or clamp to current stack. Never emit impossible amounts."
- **Condition TTL:** Prompt lacks TTL guidance for transient conditions. Fix: Add "Remove conditions after 3 turns if not narratively referenced."

### 3E — Extract Progress Prompt Audit
| Criterion | Score | Evidence (turn + quote) |
|-----------|-------|-------------------------|
| P1 | Y | System/static, user/turn-variable. |
| P2 | Y | Matches architecture. |
| P3 | Y | No redundancy. |
| P4 | Y | Schema/guidance separated. |
| P5 | Y | Clear rules. |
| P6 | Y | Concise. |
| P7 | Y | Well-formatted. |
| P8 | FAIL | Emits `done: false` for already-false objectives across 6 turns (T4, T6, T7, T9, T12, T13). Violates dedup rule. |
| P9 | PARTIAL | Needs dedup example for `done: false` states. |

**Remediation summary:**
- **Redundant objective emission:** Progress extractor repeatedly emits `done: false` for objectives that are already false. Fix: Add strict dedup rule: "Do not emit `quest_updates` for objectives already in the requested state. Only emit state changes."
- **Compaction feed:** Progress prompt does not receive compaction results, causing stale pressure/quest handling. Fix: Inject `compacted_history` into progress prompt.

### 3F — Prompt Adherence Rate Calculation
Rules: 0/13 | Narrate: 11/13 | Scene: 11/13 | State: 12/13 | Progress: 7/13
Total PASS: 41 | Total instances: 65
Rate: 41 / 65 = **0.63**

### 3G — Cross-Pipeline Redundancy Summary
- **Rules + Narrate:** 16 duplicated blocks (NPC lists, location descriptions). Intentional per architecture? No. Rules prompt should only receive `state.pc`, `state.location`, `recent_turns[-1:]`, `user_input`. Fix: Trim rules prompt to minimal scope. Estimated waste: ~400t/turn.
- **Narrate + Scene:** 1 duplicated block (location description). Intentional (scene extractor needs location context). Move on.
- **Progress + Scene:** 1 duplicated block (NPC lists). Intentional (progress needs NPC context for quest/pressure reasoning). Move on.

**Top 3 dedup opportunities:**
1. **Rules prompt:** Remove NPC/location lists. Rules only needs PC, location ID, recent turn, input.
2. **Narrate prompt:** Remove redundant `known_characters` list if `present_npcs` and `compendium` are already provided.
3. **Progress prompt:** Remove full `present_npcs` list; pass only IDs and titles relevant to active quests/pressures.

---

# SECTION 4 — Mechanic Interplay Assessment

### 4A — Beat→Narrative Loop
**Broken.** Beats generated at T3-T13 consistently override player input (T7, T10). The beat directive language is treated as a plot command rather than a flavor suggestion. Narration wanders from player intent to follow the beat, breaking the loop.

### 4B — Momentum→Directive→Tone Chain
**Loose.** Momentum deadlocks at `-3` from T5 onward. The directive and tone remain consistently desperate, but the lack of band variance means the chain never elevates or recovers. The engine fails to use momentum to modulate stakes or opportunities.

### 4C — Pressure→Stakes→Consequence Chain
**Loose.** Pressures feed into rules stakes, but consequences are purely narrative (dragging, mocking, blocking). No mechanical state changes (conditions, inventory loss, quest failure) trigger from pressure setbacks. `halden_distrust` never feeds stakes, making it mechanically inert.

### 4D — Condition→Narrative Callback
**Broken.** `bruised_ribs` and `strained_ribs` exist for 5-13 turns with zero narrative callbacks or roll modifiers. The state extractor adds them, but the rules pipeline ignores `cond_mod` and the narrator ignores the condition. Pure mechanical noise.

### 4E — Pacing Assessment
- **High-tension vs breathing:** 10/13 turns are high-tension/confrontation. Zero breathing turns. Player burnout is imminent.
- **Pressure timer alignment:** `halden_distrust` sits inert for 10 turns. Cap at 4 turns then force escalation or resolve.
- **Momentum arc:** Random oscillation with no story direction. Deadlocks at `-3`.
- **Beat type variety:** 80% `pressure`/`complication`/`escalation`. >60% same type.
- **Escape paths:** Death spiral from T5. Failed rolls only generate more pressure, never viable choices.

### 4F — NPC Entry/Exit Coherence
- `inn_patrons` and `shadowy_figure` added without explicit narration grounding (T9, T10).
- `Melvin Calloway` added T13, used for action, coherent.
- `Halden` removed T4, referenced in compendium, coherent.
- Ghost NPCs: None, but `inn_patrons` and `shadowy_figure` act as background props with no agency.

### 4G — Player Intent Fidelity
**Broken.** Narrator ignores input at T7 and T10, substituting GM beat actions. Rules pipeline correctly classifies intent, but the narrator pipeline fails to process it. Player agency is consistently overridden by backstage direction.

---

# SECTION 5 — Compaction Report

### 5A — Chronicle Quality
- **T6:** 3 bullets added. Accurate named entities. `[OK]`
- **T7-T11:** Compaction events fire but add 0 bullets. Bullets are generic or missing. `[FAIL]`
- **T12:** 6 bullets added. Accurate but include "Uneventful" filler. `[PARTIAL]`
- **T13:** Compaction event fires, adds 0 bullets. `[FAIL]`

### 5B — Sanitization Fidelity
- `quest_close`: `settle_the_debt` completed T2, but compaction at T6/T12 does not close it or note it. `[FAIL]`
- `condition_remove`: `low_morale`, `shaken`, `exhausted`, `dizzy` resolved, but compaction does not remove them from prior_history. `[FAIL]`
- `pressure_remove`: `inn_entrance_blockade`, `failed_bribe_consequence`, `inn_witness_pressure`, `thug_escalation`, `forced_abduction`, `bald_tough_retaliation` removed, but compaction sanitization log is empty. `[FAIL]`
- `inventory_remove`: `credits` removed T2, compaction does not reflect. `[FAIL]`
- `recent_events_compact`: Entries consolidated poorly, retaining stale facts. `[FAIL]`

**Sanitization Fidelity Rate:** 0 / 5 = **0.0**

### 5C — Compaction Score (1–5)
**1/5.** Bullets only added at T6 and T12. Sanitization entirely absent across all passes. Compactor is functionally broken for 80% of the run.

---

# SECTION 6 — Auto-Checker Failures

1. `universal.narrate.binding_present` (T1, T3, T5, T6, T7, T8, T9, T10, T11, T12)
   - **True failure.** Rules outcome is never fed to the narrator.
   - **Why:** Data flow bug in `run_turn()`. `rules_outcome` is computed but not injected into Step 1 user prompt.
   - **Remediation:** `bad prompt | failed to input key information`. Fix engine data flow to pass `rules_outcome` to Narrate pipeline.

2. `universal.npc_mention.extracted` (T2, T5, T7, T8, T9, T11)
   - **True failure.** Narration mentions names/entities not in scene extract.
   - **Why:** Scene extractor fails to ground ambient/observer NPCs; narrator invents names.
   - **Remediation:** `schema drift | scope/domain mismatch`. Strengthen Scene prompt grounding rule; add narrator constraint to only use extracted/known names.

3. `progress.quest_id_collision` (T2)
   - **True failure.** Progress re-emits completed quest ID.
   - **Why:** Progress prompt lacks strict dedup for `status: completed` quests.
   - **Remediation:** `bad prompt | failed to output key information`. Add hard dedup rule: "If quest status is completed, do not emit quest_updates."

---

# SECTION 7 — Per-Pipeline Mechanical Critique

### Rules Pipeline
**What Went Well:** Intent classification is accurate (T1, T3, T5, T11). Dice resolution math is correct. Anti-declare-outcome rule enforced.
**What Went Poorly:** Fails to feed `rules_outcome` to narrator (T1-T12). `cond_mod` never calculated or passed despite conditions existing.
**Prompt Adherence Failures:** None in prompt text, but data flow failure breaks adherence.
**Mechanic Ownership Check:** Correctly owns intent/dice. No misplaced mechanics.
**Scope Discipline:** Correctly limits input to PC, location, recent turn, input.
**Issues Bulleted List:**
- `- **Rules outcome not fed to Narrate** (T1-T12) — Failure mode: failed to input key information. Remediation: Update engine data flow to inject `rules_outcome` into Step 1 prompt.`
- `- **Condition modifiers ignored** (T1-T13) — Failure mode: scope/domain mismatch. Remediation: Pass `pc.conditions` to rules pipeline for `cond_mod` calculation.`
**Pipeline Score: 3/5**

### Narrate Pipeline
**What Went Well:** Prose matches pack style (second-person past, concrete details, 120-220 words). GM beat integration is structurally sound.
**What Went Poorly:** Ignores player input at T7 and T10 to follow GM beat. Fails to bind dice outcome to prose register.
**Prompt Adherence Failures:** Violates "Player input is truth" at T7, T10. Violates "Honor the dice" at T3, T5, T11 (narration describes success despite fail/setback bands).
**Mechanic Ownership Check:** Correctly owns prose. No misplaced mechanics.
**Scope Discipline:** Correctly uses rich inputs.
**Issues Bulleted List:**
- `- **Narrator ignores player input** (T7, T10) — Failure mode: bad prompt. Remediation: Add explicit priority rule: "Player input dictates action; GM beat dictates flavor only."`
- `- **Dice outcome not bound to prose** (T3, T5, T11) — Failure mode: failed to input key information. Remediation: Inject `rules_outcome.band` and `directive` into narrate prompt.`
**Pipeline Score: 2/5**

### Extract Scene Pipeline
**What Went Well:** Accurately tracks NPC presence/attitude shifts. Location changes extracted correctly.
**What Went Poorly:** Adds ungrounded NPCs (`inn_patrons`, `shadowy_figure`) without narration/compendium grounding.
**Prompt Adherence Failures:** Violates "NPC Grounding Rule" at T9, T10.
**Mechanic Ownership Check:** Correctly owns scene/NPC/location. No misplaced mechanics.
**Scope Discipline:** Correctly skips when no scene events.
**Issues Bulleted List:**
- `- **Ungrounded NPC addition** (T9, T10) — Failure mode: schema drift. Remediation: Strengthen grounding rule to require explicit narration mention or compendium ID match.`
**Pipeline Score: 3/5**

### Extract State Pipeline
**What Went Well:** Accurately extracts inventory deltas and condition lifecycles. ID normalization correct.
**What Went Poorly:** Emits `inventory_remove` with amount exceeding stack at T13. Relies on validator to clamp.
**Prompt Adherence Failures:** Violates "Read current stack" rule at T13.
**Mechanic Ownership Check:** Correctly owns inventory/conditions. No misplaced mechanics.
**Scope Discipline:** Correctly skips when no state events.
**Issues Bulleted List:**
- `- **Overdraw emission** (T13) — Failure mode: bad prompt. Remediation: Add hard rule: "If requested remove amount > current stack, clamp to current stack or emit null. Never emit impossible amounts."`
**Pipeline Score: 3/5**

### Extract Progress Pipeline
**What Went Well:** Accurately generates GM beats and scene pressures. Quest objective tracking works when state changes.
**What Went Poorly:** Repeatedly emits `done: false` for already-false objectives (T4, T6, T7, T9, T12, T13). Compaction feed is broken.
**Prompt Adherence Failures:** Violates dedup rule across 6 turns.
**Mechanic Ownership Check:** Correctly owns quests/pressures/beats. No misplaced mechanics.
**Scope Discipline:** Correctly skips when no progress events.
**Issues Bulleted List:**
- `- **Redundant objective emission** (T4, T6, T7, T9, T12, T13) — Failure mode: bad prompt. Remediation: Add strict dedup: "Do not emit quest_updates for objectives already in the requested state."`
**Pipeline Score: 2/5**

---

# SECTION 8 — Cross-Pipeline Correlation

### Rules → Narrate Binding
**Broken.** `rules_outcome` is never fed to Narrate (T1-T12). Dice bands and directives do not shape prose register. Narration ignores mechanical outcomes.

### Rules → Extract State Routing
**Broken.** `stakes` and `band` are fed to State extractor, but conditions added by State extractor never feed back into Rules `cond_mod`. State and Rules are decoupled.

### Narrate → Scene Extract Consistency
**Loose.** NPC enter/exit narrated → scene extract captures it. However, scene extract adds ungrounded NPCs (T9, T10) that narration does not explicitly name, creating drift.

### Narrate → State Extract Consistency
**Tight.** Inventory/condition changes narrated → state extract captures them accurately. T13 overdraw is a prompt failure, not a consistency failure.

### Narrate → Progress Extract Consistency
**Loose.** Quest/pressure changes narrated → progress extract captures them. However, progress extractor emits redundant `done: false` updates, polluting the state feed.

### Progress → Narrate Feedback Loop
**Broken.** `gm_beat` from T-N surfaces in narration T-(N+1), but the beat directive overrides player input instead of shaping flavor. `scene_pressure_add` feeds rules context, but pressures never mechanically escalate stakes.

---

# SECTION 9 — Storytelling Criteria (SECONDARY)

### quest_arc_quality
Quests form a compelling initial arc with `settle_the_debt`, but stall completely afterward. `deliver_the_ledger` and `clear_the_road_toughs` objectives are never completed or failed, leaving the player in a static loop. Completion/failure does not create interesting consequences because the engine never generates new objectives or advances stalled arcs.

### rewards_and_consequences [trace]
Successes produce minimal positive outcomes; failures produce dead-end pressure. Momentum deadlocks at `-3`, and conditions accumulate without mechanical or narrative payoff. The pattern in 1A and 1D shows a consistent failure to convert setbacks into interesting options or successes into meaningful rewards.

### world_consistency
Most entities are sanctioned by the engine or player input. However, the narrator and scene extractor introduce `inn_patrons` and `shadowy_figure` without grounding, creating unsanctioned introductions that break world consistency. The engine's compendium is underutilized for NPC identity resolution.

### failure_arc [trace]
Failures create a death spiral rather than interesting options. Pressures stack without resolution, momentum stays at `-3`, and conditions pile up. The engine fails to provide escape paths or de-escalation mechanics, turning failures into dead ends rather than branching narrative paths.

---

# SECTION 10 — Verdicts

### V1 — Mechanical Integrity → 2/5
Major extraction bugs in the progress pipeline (redundant `done: false` emissions) and state pipeline (overdraw emission) pollute state. Momentum deadlocks at `-3`, conditions lack mechanical modifiers, and compaction sanitization is entirely absent. The weakest pipeline is Progress, followed by State.

### V2 — Narrative Quality → 3/5
Prose is competent and matches the pack style, but consistently ignores player input to follow GM beats (T7, T10). Dice outcomes are not bound to prose register. The narrative is mechanically driven but narratively disjointed.

### V3 — System Cohesion → 2/5
Pipelines fight each other: GM beats override player input, conditions exist in state but never feed rules, and compaction silently fails to add bullets for 80% of the run. The engine behaves as isolated pipelines rather than a cohesive system.

### V4 — Prompt Quality → 2/5
Prompt architecture allows redundant emissions, missing data flows, and weak grounding rules. The highest-priority fix is injecting `rules_outcome` into the Narrate prompt and adding strict dedup for progress objectives.

### V5 — Compaction → 1/5
Compactor only adds bullets at T6 and T12. Sanitization for quests, conditions, pressures, and inventory is entirely absent across all passes. The compactor is functionally broken for the majority of the run.

### V6 — Pipeline I/O Relevance
- **Rules:** Inputs are appropriately minimal. Output is correct but not routed.
- **Narrate:** Inputs are rich but missing `rules_outcome`. Output ignores player input.
- **Scene:** Inputs include unnecessary compendium lists. Output adds ungrounded NPCs.
- **State:** Inputs are correct. Output emits impossible amounts.
- **Progress:** Inputs are complex but missing compaction feed. Output emits redundant state.
**Score: 2/5**

### V7 — Key Findings
The engine's core failure is a broken data flow: `rules_outcome` is never fed to the Narrate pipeline, breaking the dice-band binding loop (T1-T12). The Progress pipeline repeatedly emits redundant `done: false` quest updates, polluting state. Compaction silently fails to add bullets or sanitize state for 80% of the run. The highest-priority fix is correcting the Rules→Narrate data injection and adding strict dedup rules to the Progress prompt.

---

# SECTION 11 — Actionable Issues

**Critical:**
- `- **Rules outcome not fed to Narrate** (T1-T12) — Failure mode: failed to input key information. Remediation: Update engine data flow to inject `rules_outcome` into Step 1 prompt.`
- `- **Compaction fails to add bullets/sanitize** (T7-T11, T13) — Failure mode: bad prompt | scope/domain mismatch. Remediation: Fix compactor trigger logic to append bullets on every compaction event and enforce sanitization rules for quests/conditions/pressures.`
- `- **Narrator ignores player input** (T7, T10) — Failure mode: bad prompt. Remediation: Add explicit priority rule: "Player input dictates action; GM beat dictates flavor only. Never substitute player action."`

**Major:**
- `- **Progress emits redundant done: false** (T4, T6, T7, T9, T12, T13) — Failure mode: bad prompt. Remediation: Add strict dedup: "Do not emit quest_updates for objectives already in the requested state."`
- `- **Conditions never feed rules/narration** (T1-T13) — Failure mode: scope/domain mismatch. Remediation: Pass `pc.conditions` to Rules for `cond_mod` calculation and add Narrator rule to reference active conditions.`
- `- **Ungrounded NPC addition** (T9, T10) — Failure mode: schema drift. Remediation: Strengthen Scene prompt grounding rule to require explicit narration mention or compendium ID match before `npc_add`.`

**Minor:**
- `- **Overdraw emission** (T13) — Failure mode: bad prompt. Remediation: Add hard rule: "If requested remove amount > current stack, clamp to current stack. Never emit impossible amounts."`
- `- **Momentum deadlocks at -3** (T5-T13) — Failure mode: failed to output key information. Remediation: Add momentum recovery band examples and de-escalation directive to Rules prompt.`

## Auto-Checker

**129 passed, 25 failed**

| Turn | Assertion | Result | Detail |
|---|---|---|---|
| 1 | `rules.rolled` | ❌ | rolled=True |
| 1 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 1 | `universal.pending_gm_beat.consumed` | ✅ | (first turn) |
| 1 | `universal.location_change.applied` | ✅ | (no change) |
| 1 | `universal.narrate.binding_present` | ❌ | rolled=true but narrate user prompt did not include rules_outcome BINDING block |
| 1 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 1 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 1 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 1 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 1 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 1 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 2 | `rules.rolled` | ❌ | rolled=False |
| 2 | `extract.state.inventory_remove` | ✅ | inventory_remove[credits] amount=500 |
| 2 | `extract.progress.quest_updates` | ✅ | quest_updates[settle_the_debt] found |
| 2 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 2 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 2 | `universal.location_change.applied` | ✅ | (no change) |
| 2 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 2 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Finally', 'Credits'] |
| 2 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 2 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 2 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 2 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 2 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 2 | `progress.quest_id_collision` | ❌ | quest_updates re-creates already-completed quest id='settle_the_debt' |
| 3 | `rules.rolled` | ✅ | rolled=True |
| 3 | `extract.progress.quest_updates` | ✅ | quest_updates[deliver_the_ledger] found |
| 3 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=3 |
| 3 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 3 | `universal.location_change.applied` | ✅ | marrows_crossing -> marrows_crossing_well |
| 3 | `universal.narrate.binding_present` | ❌ | rolled=true but narrate user prompt did not include rules_outcome BINDING block |
| 3 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 3 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 3 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 3 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 3 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 3 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 4 | `rules.rolled` | ✅ | rolled=False |
| 4 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=4 |
| 4 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 4 | `universal.location_change.applied` | ✅ | marrows_crossing_well -> merchant_road_east |
| 4 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 4 | `universal.npc_mention.extracted` | ✅ | 4 candidates skipped (likely locations/items, not NPCs) |
| 4 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 4 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 4 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 4 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 4 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 5 | `rules.rolled` | ✅ | rolled=True |
| 5 | `extract.scene.scene_tags` | ❌ | scene_tags[combat] not found |
| 5 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=5 |
| 5 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 5 | `universal.location_change.applied` | ✅ | (no change) |
| 5 | `universal.narrate.binding_present` | ❌ | rolled=true but narrate user prompt did not include rules_outcome BINDING block |
| 5 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Otherwise', 'Crossed'] |
| 5 | `universal.recent_events.ring_bounded` | ✅ | 6 entries |
| 5 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 5 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 5 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 5 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 6 | `rules.rolled` | ✅ | rolled=True |
| 6 | `extract.state.inventory_remove` | ❌ | inventory_remove[credits] not found |
| 6 | `extract.progress.quest_updates` | ✅ | quest_updates[clear_the_road_toughs] found |
| 6 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 6 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 6 | `universal.location_change.applied` | ✅ | (no change) |
| 6 | `universal.narrate.binding_present` | ❌ | rolled=true but narrate user prompt did not include rules_outcome BINDING block |
| 6 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 6 | `universal.recent_events.ring_bounded` | ✅ | 2 entries |
| 6 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 6 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 6 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 6 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 7 | `extract.progress.quest_updates` | ✅ | quest_updates[deliver_the_ledger] found |
| 7 | `extract.progress.quest_status` | ❌ | quest[deliver_the_ledger].status='active' (expected 'completed') |
| 7 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 7 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 7 | `universal.location_change.applied` | ✅ | (no change) |
| 7 | `universal.narrate.binding_present` | ❌ | rolled=true but narrate user prompt did not include rules_outcome BINDING block |
| 7 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 7 | `universal.recent_events.ring_bounded` | ✅ | 2 entries |
| 7 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 7 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 7 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 7 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 8 | `rules.rolled` | ✅ | rolled=True |
| 8 | `extract.state.inventory_remove` | ❌ | inventory_remove[brass_key] not found |
| 8 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=8 |
| 8 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 8 | `universal.location_change.applied` | ✅ | (no change) |
| 8 | `universal.narrate.binding_present` | ❌ | rolled=true but narrate user prompt did not include rules_outcome BINDING block |
| 8 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 8 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 8 | `universal.scene.npc_cap` | ✅ | 5 NPCs |
| 8 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 8 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 8 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 9 | `rules.rolled` | ✅ | rolled=True |
| 9 | `extract.scene.scene_tags` | ❌ | scene_tags[social] not found |
| 9 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 9 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 9 | `universal.location_change.applied` | ✅ | (no change) |
| 9 | `universal.narrate.binding_present` | ❌ | rolled=true but narrate user prompt did not include rules_outcome BINDING block |
| 9 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Shadowy', 'Figure', 'Inside'] |
| 9 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 9 | `universal.scene.npc_cap` | ✅ | 5 NPCs |
| 9 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 9 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 9 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 10 | `rules.rolled` | ✅ | rolled=True |
| 10 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 10 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 10 | `universal.location_change.applied` | ✅ | (no change) |
| 10 | `universal.narrate.binding_present` | ❌ | rolled=true but narrate user prompt did not include rules_outcome BINDING block |
| 10 | `universal.npc_mention.extracted` | ✅ | 4 candidates skipped (likely locations/items, not NPCs) |
| 10 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 10 | `universal.scene.npc_cap` | ✅ | 5 NPCs |
| 10 | `universal.pc.condition_no_dupes` | ✅ | 3 conditions, no dupes |
| 10 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 10 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 11 | `rules.rolled` | ✅ | rolled=True |
| 11 | `extract.scene.scene_tags` | ✅ | scene_tags[combat] found |
| 11 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=11 |
| 11 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 11 | `universal.location_change.applied` | ✅ | (no change) |
| 11 | `universal.narrate.binding_present` | ❌ | rolled=true but narrate user prompt did not include rules_outcome BINDING block |
| 11 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Shadowy', 'Figure', 'Inside'] |
| 11 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 11 | `universal.scene.npc_cap` | ✅ | 5 NPCs |
| 11 | `universal.pc.condition_no_dupes` | ✅ | 3 conditions, no dupes |
| 11 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 11 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 12 | `rules.rolled` | ❌ | rolled=True |
| 12 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 12 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 12 | `universal.location_change.applied` | ✅ | merchant_road_east -> rear_courtyard |
| 12 | `universal.narrate.binding_present` | ❌ | rolled=true but narrate user prompt did not include rules_outcome BINDING block |
| 12 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 12 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 12 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 12 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 12 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 12 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 13 | `rules.rolled` | ✅ | rolled=False |
| 13 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=13 |
| 13 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 13 | `universal.location_change.applied` | ✅ | (no change) |
| 13 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 13 | `universal.npc_mention.extracted` | ✅ | 4 candidates skipped (likely locations/items, not NPCs) |
| 13 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 13 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 13 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 13 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 13 | `universal.momentum.band_delta` | ✅ | (no roll) |

## Turn Metrics

| # | input | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | retries | parse_fail | duration_s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | Walk over to Caron's table and sit down across f… | 1403 | 2677 | 2452 | 2929 | 3940 | 0 | 0 | 32.29 |
| 2 | I slide 500 credits across the table to Caron an… | 1808 | 3020 | 2828 | 2946 | 4280 | 0 | 0 | 29.07 |
| 3 | I find Halden by the town well and offer to carr… | 1825 | 3369 | 2878 | 2936 | 4344 | 0 | 0 | 33.54 |
| 4 | I leave Marrow's Crossing by the east gate and h… | 1804 | 3801 | 2635 | 2783 | 4069 | 0 | 0 | 29.89 |
| 5 | I walk up to the two toughs at the inn door and … | 1662 | 3762 | 2697 | 2983 | 4230 | 0 | 0 | 39.97 |
| 6 | I drop 200 credits on the ground between the tou… | 1906 | 3958 | 2908 | 2914 | 4491 | 0 | 0 | 46.81 |
| 7 | I sit across from Halden at his table, slide the… | 1825 | 4062 | 2830 | 2909 | 4415 | 0 | 0 | 38.25 |
| 8 | I pull out the brass key Halden gave me and try … | 1857 | 4209 | 2892 | 2923 | 4458 | 0 | 0 | 38.88 |
| 9 | I press my ear against the inn's stone wall and … | 1890 | 4264 | 3009 | 2900 | 4635 | 0 | 0 | 31.23 |
| 10 | I approach Matthew Estrada at the bar, grab his … | 1869 | 4224 | 3100 | 3010 | 4677 | 0 | 0 | 34.70 |
| 11 | Matthew's bodyguard draws a knife! I tackle him … | 1978 | 4277 | 3072 | 2893 | 4675 | 0 | 0 | 35.04 |
| 12 | I grab the ledger from my coat and sprint out th… | 1832 | 4247 | 2982 | 2966 | 4554 | 0 | 0 | 44.57 |
| 13 | I find a quiet corner at the dock and wrap my wo… | 1797 | 4246 | 2842 | 3003 | 4363 | 0 | 0 | 35.32 |
|  | TOTALS | 23456 | 50116 | 37125 | 38095 | 57131 | 0 | 0 | 469.56 |

**Total turns:** 13 · **Total duration:** 469.56s · **Avg/turn:** 36.12s
**Total tokens in:** 205,923 · **Total tokens out:** 171,805 · **Total LLM time:** 450.5s
**Total retries:** 0 · **Total parse failures:** 0

