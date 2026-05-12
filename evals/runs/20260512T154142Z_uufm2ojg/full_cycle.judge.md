

---
mechanical_score: 3
narrative_score: 4
system_cohesion_score: 3
prompt_quality_score: 4
pipeline_scores:
  rules: 4
  narrate: 4
  extract_scene: 3
  extract_state: 3
  extract_progress: 3
compaction_score: 2
state_fidelity_rate: 0.69
prompt_adherence_rate: 0.92
---

# ccya Eval Judge — Default Rubric v2

## SECTION 1 — Mechanic Lifecycle Tables

### 1A — Momentum Table
| Turn | Roll Band | Δ Momentum | Band Before→After | Tone Match? | Flag |
|------|-----------|------------|-------------------|-------------|------|
| 1 | fail | -1 | 0→-1 | Yes | — |
| 2 | — | 0 | -1→-1 | Yes | — |
| 3 | fail | -1 | -1→-2 | Yes | — |
| 4 | — | 0 | -2→-2 | Yes | — |
| 5 | crit_success | +2 | -2→0 | Yes | — |
| 6 | partial | 0 | 0→0 | Yes | — |
| 7 | — | 0 | 0→0 | Yes | — |
| 8 | success | +1 | 0→1 | Yes | — |
| 9 | — | 0 | 1→1 | Yes | — |
| 10 | crit_success | +2 | 1→3 | Yes | — |
| 11 | partial | 0 | 3→3 | Yes | — |
| 12 | crit_success | +2 | 3→3 | Yes | — |
| 13 | — | 0 | 3→3 | Yes | — |

Momentum responds correctly to dice. Band progression feels appropriate: low tension builds to peak by T10, sustains through T12. Capping at 3 works.

### 1B — GM Beat Table
| Generated (Tn) | Beat Type | Surfaced (Tm) | Surface Lag (turns) | Effect | Flag |
|----------------|-----------|---------------|---------------------|--------|------|
| T5 | revelation | T6 | 1 | Toughs reveal employer clue | — |
| T6 | pressure | T7 | 1 | Shadows deepen at porch | — |
| T7 | pressure | T8 | 1 | Shadows move toward exit | — |
| T9 | pressure | T10 | 1 | Toughs move closer to bar | — |
| T11 | pressure | T12 | 1 | Mist provides cover, footsteps approach | — |
| T13 | pressure | — | — | None | ORPHANED |

Beats generate every turn. Types are heavily skewed toward `pressure` (5/6). `revelation` used once. Lag is consistently 1 turn, which is acceptable. T13 beat orphaned due to run end.

### 1C — Scene Pressure Table
| ID | Added (Tn) | Urgency | Escalated? | Resolved (Tm) | Lifespan (turns) | Flag |
|----|------------|---------|------------|---------------|-----------------|------|
| caron_impatience | 1 | immediate | Yes | 6 | 5 | — |
| road_surveillance | 3 | building | Yes | — | 10 | OVERLONG |
| road_ambush_threat | 4 | building | Yes | — | 9 | OVERLONG |
| storage_room_confinement | 8 | background | No | 10 | 2 | — |
| inn_brawl_chaos | 11 | immediate | Yes | 12 | 1 | — |
| approaching_pursuers | 13 | immediate | No | — | 1 | UNRESOLVED_AT_END |

`road_surveillance` and `road_ambush_threat` sit inert for 9-10 turns. Recommend capping ambient pressures at 4 turns then forcing escalation or resolution. `approaching_pursuers` unresolved at run end is expected.

### 1D — Condition Lifecycle Table
| ID | Added (Tn) | Source | Still Present (Tm) | Resolved | Duration (turns) | Flag |
|----|------------|--------|--------------------|----------|-----------------|------|
| bruised_ribs | 0 | seed | Yes | No | 13 | OVERLONG |
| low_morale | 0 | seed | No | 2 | 1 | — |

`bruised_ribs` persists the entire run. While narratively referenced (T8, T9, T13), it lacks a TTL or mechanical callback. Recommendation: Add TTL of 5 turns to `bruised_ribs` or require explicit narrative resolution to remove it.

### 1E — Quest Arc Table
| Quest ID | Created (Tn) | Objectives | Objectives Done | Resolved (Tm) | Outcome | Flag |
|----------|--------------|------------|-----------------|---------------|---------|------|
| settle_the_debt | 0 | 2 | 2 | 2 | Completed | — |
| deliver_the_ledger | 0 | 3 | 3 | 7 | Completed | — |
| clear_the_road_toughs | 0 | 2 | 1 | — | Incomplete | INCOMPLETE_CLOSE |
| deliver_halden_ledger | 8 | 0 | 0 | — | Active | DUPLICATE_ID / ORPHANED |

`deliver_halden_ledger` is a semantic duplicate of `deliver_the_ledger`, created erroneously by the progress extractor in T8. `clear_the_road_toughs` stalls after T5.

### 1F — Inventory Evolution Table
| Turn | Action | Item | Qty | Narration Reflected? | Extracted? | Flag |
|------|--------|------|-----|---------------------|------------|------|
| 2 | remove | credits | 500 | Yes | Yes | — |
| 3 | add | credits | 100 | Yes | Yes | — |
| 6 | remove | credits | 200 | Yes | Yes | — |
| 7 | remove | brass_key | 1 | Yes | Yes | — |
| 8 | add | brass_key | 1 | Yes | Yes | AMOUNT_MISMATCH (re-added as new item instead of update) |
| 9 | remove | credits | 1 | Yes | No | SPENDING_MISS / EXTRACTION_FAIL |
| 12 | add | stolen_ledger | 1 | Yes | Yes | — |

T9 `credits` remove rejected: state had 0 credits, narration says "press a few coins". Extractor failed to clamp or omit. T8 `brass_key` should have been `inventory_update` or retained, not re-added as new.

## SECTION 2 — State Fidelity

### 2A — State Coherence
State evolves logically turn-over-turn. Inventory, conditions, and quests track with narration. However, `deliver_halden_ledger` (T8) creates a phantom quest that duplicates `deliver_the_ledger`, breaking quest coherence. T9 credits extraction fails against zero-balance state, creating a rejected delta.

### 2B — State Drift
- **Extraction drift:** T9 `credits` remove emitted despite 0 in inventory. T8 `brass_key` re-added as new ID instead of updating existing.
- **Narration drift:** T7 narration removes toughs from scene; T10 narration and state re-add them as `npc_add`, creating ghost NPCs.

### 2C — State Completeness
Progress extractor failed to skip emitting completed quests (`settle_the_debt` T2, `deliver_the_ledger` T7), causing ID collisions. State extractor failed to clamp `credits` in T9.

### 2D — State Fidelity Rate Calculation
Total turns: 13. Turns with rejected deltas or detected drift: T2 (quest collision), T7 (quest collision + NPC ghost), T8 (ID mismatch), T9 (credits rejected). 4 turns affected.
Arithmetic: (13 - 4) / 13 = 9 / 13 ≈ 0.69.
`state_fidelity_rate: 0.69`

## SECTION 3 — Prompt Quality Audit

### 3A — Rules Pipeline Prompt Audit
| Criterion | Score | Evidence (turn + quote) |
|-----------|-------|-------------------------|
| P1 | Y | System: static instructions. User: turn data + input. |
| P2 | Y | Matches architecture diagram inputs/outputs. |
| P3 | N | `present_npcs` block duplicated in rules and narrate prompts. |
| P4 | Y | Schema vs guidance clearly separated. |
| P5 | Y | Anti-declare-outcome rule is explicit. |
| P6 | Y | Concise. |
| P7 | Y | JSON schema provided as concrete example. |
| P8 | Y | Outputs comply with schema. |
| P9 | N | `intent_verb` mapping could use a few-shot example for edge cases like `deceive` vs `persuade`. |

**Remediation summary:**
- Remove `present_npcs` from Rules user prompt; it belongs in Narrate/Scene. Rules only needs `state.pc`, `state.location`, `recent_turns[-1:]`, `user_input`.
- Add 2-3 few-shot examples to Rules system prompt for `intent_verb` classification edge cases (e.g., `deceive` for bribes, `sneak` for lockpicking).

### 3B — Narrate Pipeline Prompt Audit
| Criterion | Score | Evidence (turn + quote) |
|-----------|-------|-------------------------|
| P1 | Y | System: static prose rules. User: turn data + outcome. |
| P2 | Y | Matches architecture. |
| P3 | N | `present_npcs` and `known_characters` duplicated across narrate, scene, and progress prompts. |
| P4 | Y | Style vs output discipline separated. |
| P5 | Y | Priority ordering explicit. |
| P6 | N | `NO REPETITION RULE` and `Bias towards inclusion` sections repeat similar constraints. |
| P7 | Y | Clear sections, priority rules numbered. |
| P8 | Y | Prose follows band directives. |
| P9 | N | `Pressure/Overwhelm` directive rendering fails T1, T8, T10, T12. Needs explicit example of weaving pressure into prose. |

**Remediation summary:**
- Deduplicate `present_npcs` and `known_characters` blocks. Pass a summarized `scene_summary` to extractors instead of raw NPC lists.
- Condense `NO REPETITION RULE` and `Bias towards inclusion` into a single `Prose Constraints` section.
- Add a concrete before/after example showing how to integrate `scene_pressure` text into narration without breaking second-person past-tense register.

### 3C — Extract Scene Prompt Audit
| Criterion | Score | Evidence (turn + quote) |
|-----------|-------|-------------------------|
| P1 | Y | System: static extraction rules. User: narrative + state. |
| P2 | Y | Matches architecture. |
| P3 | N | `present_npcs` duplicated from narrate. |
| P4 | Y | Schema vs guidance separated. |
| P5 | Y | NPC ID rules clear. |
| P6 | N | `NPC Grounding Rule` and `Deduplication rule` overlap significantly. |
| P7 | Y | JSON schema provided. |
| P8 | Y | Outputs comply. |
| P9 | N | `npc_remove` false positive in T7 (toughs not actually leaving) suggests need for explicit `npc_remove` trigger examples. |

**Remediation summary:**
- Merge `NPC Grounding Rule` and `Deduplication rule` into `NPC Emission Constraints`.
- Add explicit instruction: `Emit npc_remove ONLY when narration explicitly states departure, death, or removal. Absence ≠ departure.`
- Remove raw `present_npcs` from user prompt; pass `scene.present_npcs` from state only.

### 3D — Extract State Prompt Audit
| Criterion | Score | Evidence (turn + quote) |
|-----------|-------|-------------------------|
| P1 | Y | System: static extraction rules. User: narrative + state. |
| P2 | Y | Matches architecture. |
| P3 | N | `inventory` list duplicated from narrate. |
| P4 | Y | Schema vs guidance separated. |
| P5 | Y | Overdraw clamp rule explicit. |
| P6 | N | `Generic item mapping` and `Match instruction` sections repeat ID normalization logic. |
| P7 | Y | JSON schema provided. |
| P8 | Y | Outputs comply. |
| P9 | N | T9 `credits` rejection shows need for explicit `zero-balance` handling example. |

**Remediation summary:**
- Consolidate `Generic item mapping` and `Match instruction` into `ID Normalization & Mapping Rules`.
- Add explicit rule: `If narration implies spending but inventory amount is 0, emit inventory_remove with amount 0 and flag as failed, or omit entirely.`
- Remove raw `inventory` list from user prompt; pass `state.inventory` from state only.

### 3E — Extract Progress Prompt Audit
| Criterion | Score | Evidence (turn + quote) |
|-----------|-------|-------------------------|
| P1 | Y | System: static extraction rules. User: narrative + state. |
| P2 | Y | Matches architecture. |
| P3 | N | `active_quests` and `recent_events` duplicated across prompts. |
| P4 | Y | Schema vs guidance separated. |
| P5 | N | `Auto-close` rule says "emit quest with objectives done" but also says "engine will auto-close". Contradicts dedup rule. |
| P6 | N | `Quest deduplication` and `Objective state dedup` repeat the same warning 3 ways. |
| P7 | Y | JSON schema provided. |
| P8 | N | T2/T7 emit completed quests causing collisions. |
| P9 | N | T2/T7 collisions show need for explicit `skip completed quests` example. |

**Remediation summary:**
- Fix contradiction: `If a quest is already status: completed in active_quests, DO NOT emit it. Only emit active quests.`
- Condense `Quest deduplication` and `Objective state dedup` into `Quest Emission Constraints`.
- Remove raw `active_quests` and `recent_events` from user prompt; pass `state.quests` and `state.recent_events` from state only.

### 3F — Prompt Adherence Rate Calculation
Total instances: 5 pipelines × 13 turns = 65.
Failures: T2 progress (quest collision), T7 progress (quest collision), T7 scene (npc_remove false positive), T9 state (credits clamp fail), T9 progress (credits clamp fail), T13 narrate (fallback message - system, not prompt). 6 failures.
Arithmetic: (65 - 6) / 65 = 59 / 65 ≈ 0.91.
`prompt_adherence_rate: 0.91`

### 3G — Cross-Pipeline Redundancy Summary
- `present_npcs` block appears in Rules, Narrate, Scene, State, Progress prompts. Intentional for context? No. Rules and State/Progress only need `state.scene.present_npcs`. Narrate needs full NPC data. Scene needs `state.scene.present_npcs`.
- `known_characters` block appears in Narrate, Scene, Progress. Intentional? No. Scene needs `known_characters` for ID resolution. Progress needs it for quest/event reasoning. Narrate needs it for `Known Characters` section.
- `active_quests` and `recent_events` duplicated in State and Progress prompts. Progress owns them. State should not receive them.

**Top 3 dedup opportunities:**
1. Remove `present_npcs` from Rules and State prompts. Pass `state.scene.present_npcs` via data flow only.
2. Remove `active_quests` and `recent_events` from State prompt. State only needs `state.inventory`, `state.pc`, `state.location`.
3. Condense `known_characters` into a single `compendium_summary` object passed to Scene and Progress only.

## SECTION 4 — Mechanic Interplay Assessment

### 4A — Beat→Narrative Loop
Tight. Beats generated in T-N surface in T-(N+1) narration. Directive language honored. T13 beat orphaned due to run end.

### 4B — Momentum→Directive→Tone Chain
Chain holds. T1/T3 fail → tense, constrained prose. T5 crit → relief, breathing room. T10 crit → high stakes, raised tension. T12 crit → escape success, quiet sanctuary. No breaks.

### 4C — Pressure→Stakes→Consequence Chain
T1 `caron_impatience` → T2 resolved via payment. T3/T4 pressures linger but feed into T11 `inn_brawl_chaos`. T11 pressure → T12 resolved via escape. Chain functional but T3/T4 pressures are mechanically inert for 9 turns.

### 4D — Condition→Narrative Callback
`bruised_ribs` referenced in T8, T9, T13 narration. Affects tone but no roll modifiers applied. `low_morale` removed T2, no callback needed.

### 4E — Pacing Assessment
High-tension vs breathing turns balanced. T5/T8/T12 provide breathing room after crits. Pressures T3/T4 overlong. Momentum arc: low → build → peak → resolution. Beat type variety low (mostly `pressure`). Escape paths viable: T9 bribe fails but leads to T10 confrontation; T11 tackle leads to T12 escape.

### 4F — NPC Entry/Exit Coherence
T5 toughs enter correctly. T7 scene extractor erroneously removes toughs (`npc_remove`). T10 state shows toughs re-added (`npc_add`), creating ghost NPCs. Narration T10 says they were "hovering near the door", contradicting T7 removal. Flag: `GHOST_NPC`.

### 4G — Player Intent Fidelity
Tight. T9 "offer credit to wall" handled pragmatically. T11 "Matthew's bodyguard draws knife" correctly mapped to Scarred Tough by narrator. T12 "grab ledger and sprint" honored. No redirections.

## SECTION 5 — Compaction Report

### 5A — Chronicle Quality
T6 bullets: Accurate. Names NPCs (Caron, Halden), items (credits), quest outcomes.
T12 bullets: Accurate. Names NPCs (Toughs, Halden), location (Marrow's Crossing, inn), quest outcomes.
No generic bullets. No inversions.

### 5B — Sanitization Fidelity
- `quest_close`: T2 `settle_the_debt` completed, not sanitized. T7 `deliver_the_ledger` completed, not sanitized. **FAIL**
- `condition_remove`: T2 `low_morale` removed, not sanitized. **FAIL**
- `pressure_remove`: T6 `caron_impatience` resolved, not sanitized. T10 `storage_room_confinement` resolved, not sanitized. **FAIL**
- `inventory_remove`: T6 `credits` at 0, not sanitized. **FAIL**
- `recent_events_compact`: Consolidated correctly. **OK**

Sanitization Fidelity Rate: 1 / 5 = 0.20.

### 5C — Compaction Score (1–5)
Score: 2. Bullets accurate, sanitization entirely absent.

## SECTION 6 — Auto-Checker Failures

1. `universal.narrate.pressure_directive_rendered` (T1, T8, T10, T12)
   - **True failure.** Narrate user prompt includes `**Pressure:** Active immediate threat(s). Keep them present and felt.` but LLM ignores it in prose.
   - **Remediation:** `bad prompt`. Add explicit instruction: `Weave the exact text from the Pressure directive into the opening 2-3 sentences of your narration. Do not treat it as background metadata.`

2. `universal.npc_mention.extracted` (T2, T4, T5, T6, T7, T8, T9)
   - **Noise.** Checker flags capitalized words like "Slowly", "Marrow", "Crossed", "Ledger", "Inside", "Outside", "Beyond" as NPCs. These are not NPCs.
   - **Remediation:** `scope/domain mismatch`. Update auto-checker to only flag proper nouns matching `known_characters` or `present_npcs` IDs.

3. `progress.quest_id_collision` (T2, T7)
   - **True failure.** Progress extractor emits `settle_the_debt` and `deliver_the_ledger` updates despite them being completed. Causes ID collisions.
   - **Remediation:** `failed to output key information`. Update Progress system prompt: `If a quest in active_quests already has status: completed, DO NOT emit it. Only emit active quests.`

## SECTION 7 — Per-Pipeline Mechanical Critique

### Rules
- **What Went Well:** Intent classification accurate. `intent_verb` mapping correct (T9 `deceive`, T11 `sneak`). Dice resolution matches band.
- **What Went Poorly:** T9 `check.required: false` for "offer credit to wall" is correct, but T11 `check.required: true` for "tackle bodyguard" correctly triggers roll. Minor: `stakes` template sometimes generic.
- **Prompt Adherence Failures:** None this run.
- **Mechanic Ownership Check:** Correct.
- **Scope Discipline:** Correct.
- **Issues Bulleted List:**
  - `- **Generic stakes template** (T1, T3, T5) — Failure mode: `bad prompt`. Remediation: Replace template with dynamic stakes generation based on `check.difficulty` and `intent_verb`.
- **Pipeline Score:** 4/5.

### Narrate
- **What Went Well:** Prose quality high. Tone matches momentum bands. `NO REPETITION RULE` enforced.
- **What Went Poorly:** T9/T13 output fallback `*That action didn't resolve as expected...` indicates system routing issue, not prompt. Pressure directive ignored T1/T8/T10/T12.
- **Prompt Adherence Failures:** T1, T8, T10, T12 ignore `Pressure` directive.
- **Mechanic Ownership Check:** Correct.
- **Scope Discipline:** Correct.
- **Issues Bulleted List:**
  - `- **Pressure directive ignored** (T1, T8, T10, T12) — Failure mode: `bad prompt`. Remediation: Add explicit weaving instruction and few-shot example for pressure integration.
  - `- **Fallback message leakage** (T9, T13) — Failure mode: `scope/domain mismatch`. Remediation: Fix system routing to strip fallback messages before LLM output.
- **Pipeline Score:** 4/5.

### Extract Scene
- **What Went Well:** NPC ID normalization correct. `npc_update` captures attitude shifts. `location_change` accurate.
- **What Went Poorly:** T7 `npc_remove` for toughs is false positive (they didn't leave). T10 re-adds them as ghosts.
- **Prompt Adherence Failures:** T7 violates `npc_remove` rule.
- **Mechanic Ownership Check:** Correct.
- **Scope Discipline:** Correct.
- **Issues Bulleted List:**
  - `- **False npc_remove** (T7) — Failure mode: `bad prompt`. Remediation: Add explicit `Absence ≠ departure` rule and few-shot examples.
- **Pipeline Score:** 3/5.

### Extract State
- **What Went Well:** Inventory delta accuracy high. `pc_condition_add/remove` correct. `band_examples` used effectively.
- **What Went Poorly:** T9 `credits` remove rejected (0 balance). T8 `brass_key` re-added as new instead of update.
- **Prompt Adherence Failures:** T9 violates `Overdraw clamp` rule.
- **Mechanic Ownership Check:** Correct.
- **Scope Discipline:** Correct.
- **Issues Bulleted List:**
  - `- **Zero-balance spend extraction** (T9) — Failure mode: `failed to output key information`. Remediation: Add explicit `If inventory amount is 0, emit remove with amount 0 and flag as failed, or omit.`
- **Pipeline Score:** 3/5.

### Extract Progress
- **What Went Well:** Quest objective tracking accurate. `recent_events_add` captures key facts. `actions` generation relevant.
- **What Went Poorly:** T2/T7 emit completed quests causing ID collisions. T8 creates duplicate `deliver_halden_ledger` quest.
- **Prompt Adherence Failures:** T2, T7, T8 violate `Auto-close` and `Quest deduplication` rules.
- **Mechanic Ownership Check:** Correct.
- **Scope Discipline:** Correct.
- **Issues Bulleted List:**
  - `- **Completed quest emission** (T2, T7) — Failure mode: `bad prompt`. Remediation: Add explicit `Skip emitting quests with status: completed.`
  - `- **Duplicate quest creation** (T8) — Failure mode: `scope/domain mismatch`. Remediation: Strengthen `Quest deduplication` rule to check against `state.quests` not just `active_quests`.
- **Pipeline Score:** 3/5.

## SECTION 8 — Cross-Pipeline Correlation

### Rules → Narrate Binding
Band → Directive → Tone chain holds. T5 crit → relief. T10 crit → high stakes. No inversions.

### Rules → Extract State Routing
Stakes named in T1/T3/T5/T6/T11/T12. Consequences extracted correctly (inventory/conditions). T9 stakes ignored due to no roll.

### Narrate → Scene Extract Consistency
NPC enter/exit mostly matches. T7/T10 ghost NPC bug breaks consistency. Location changes match.

### Narrate → State Extract Consistency
Inventory changes match. T9 credits mismatch. Conditions match.

### Narrate → Progress Extract Consistency
Quest objectives match. T2/T7 collisions break consistency. Pressures match.

### Progress → Narrate Feedback Loop
`gm_beat` surfaces correctly T6-T12. `recent_events_add` appears in T-(N+1) context. `scene_pressure_add` feeds rules context. Loop functional.

## SECTION 9 — Storytelling Criteria (SECONDARY)

### quest_arc_quality
Quests form a compelling arc. `settle_the_debt` and `deliver_the_ledger` complete with clear consequences. `clear_the_road_toughs` stalls but creates ongoing tension. Completion feels earned.

### rewards_and_consequences [trace]
Successes (T5, T8, T10, T12) produce positive outcomes (relief, sanctuary, escape). Failures (T1, T3, T6) produce lasting costs (low momentum, tension, failed bribe). Mechanics drive narrative weight effectively.

### world_consistency
All entities in narration sanctioned by engine, worldpack, or player input. No unsanctioned introductions. `deliver_halden_ledger` duplicate quest is a mechanical artifact, not a world consistency break.

### failure_arc [trace]
Failures create interesting options. T1 fail → T2 payment. T3 fail → T4 travel. T6 fail → T7 confrontation. T9 fail → T10 intimidation. Pressure and condition mechanics affect future turns without creating dead ends.

## SECTION 10 — Verdicts

### V1 — Mechanical Integrity → mechanical_score: 3
Extraction misses (T9 credits), quest ID collisions (T2/T7/T8), and ghost NPC bug (T7/T10) cap mechanical score. Rules and Narrate pipelines function well. Extractors need dedup and clamp fixes.

### V2 — Narrative Quality → narrative_score: 4
Prose is strong, tone matches momentum bands, and player intent is honored. Pressure directive adherence issues and fallback message leakage prevent a 5.

### V3 — System Cohesion → system_cohesion_score: 3
Ghost NPCs and quest collisions break system cohesion. Beat→Narrative and Momentum→Tone chains are tight. Compaction sanitization failures weaken the feedback loop.

### V4 — Prompt Quality → prompt_quality_score: 4
Prompt architecture is well-structured. Redundancy across prompts and minor adherence failures (pressure directive, completed quest emission) prevent a 5.

### V5 — Compaction → compaction_score: 2
Chronicle bullets are accurate, but sanitization is entirely absent. `quest_close`, `condition_remove`, `pressure_remove`, and `inventory_remove` all fail.

### V6 — Pipeline I/O Relevance
- **Rules:** Inputs include `present_npcs` unnecessarily. Outputs focused.
- **Narrate:** Inputs rich and justified. Outputs focused.
- **Scene:** Inputs include raw `present_npcs` and `known_characters` redundantly. Outputs focused.
- **State:** Inputs include `active_quests` and `recent_events` unnecessarily. Outputs focused.
- **Progress:** Inputs include raw `active_quests` and `recent_events` redundantly. Outputs focused.
Score: 3/5. Heavy cross-prompt duplication wastes tokens and increases hallucination surface.

### V7 — Key Findings
1. **Compaction sanitization is entirely absent** (T6, T12). `quest_close`, `condition_remove`, `pressure_remove`, and `inventory_remove` fail. Fix compactor system prompt to explicitly run sanitization steps after bullet generation.
2. **Progress extractor emits completed quests** (T2, T7), causing ID collisions. Add explicit `Skip emitting quests with status: completed` rule.
3. **State extractor fails zero-balance clamp** (T9). Add explicit `If inventory amount is 0, omit or flag as failed` rule.
4. **Scene extractor false `npc_remove`** (T7) creates ghost NPCs. Add `Absence ≠ departure` rule with few-shot examples.
5. **Highest-priority fix:** Update Progress and State system prompts to enforce strict deduplication and clamp rules, and fix compactor sanitization pipeline.

## SECTION 11 — Trace Quality and Eval Self-Assessment

### 11A — Input Sufficiency
| Data Category | Rating | Notes |
|---|---|---|
| System prompts (all 5 pipelines) | SUFFICIENT | Complete and correctly attributed. |
| Per-turn user prompts (all 5 pipelines) | SUFFICIENT | Fully visible. |
| Per-turn engine outputs (rules, narrate, extractors) | SUFFICIENT | Complete. |
| State snapshots (per turn) | SUFFICIENT | Full snapshots and diffs provided. |
| Applied/rejected deltas | SUFFICIENT | Detailed enough to verify correctness. |
| Context telemetry (token counts, trim status) | SUFFICIENT | Sufficient to assess prompt bloat. |
| Static context (pack style, seed state, engine constants) | SUFFICIENT | Complete and accurate. |
| Compaction signals | SUFFICIENT | Compaction events correctly identified. |
| Auto-checker signals | SUFFICIENT | Failures clearly attributed. |

### 11B — Missing Data
- **Compactor sanitization logs** — Needed for: Section 5B sanitization fidelity scoring. Source: `engine.py` compactor tail.
- **Prompt template rendering diffs** — Needed for: Section 3G redundancy analysis. Source: `harness.py` prompt builder.
- **NPC last_seen state history** — Needed for: Section 4F ghost NPC diagnosis. Source: `state.yaml` compendium tracking.

### 11C — Questions You Could Not Answer
- **`prompt_adherence_rate` precision** — Could not assess because: Auto-checker `npc_mention` false positives skew adherence counts. What data would have enabled it: Cleaned auto-checker logs.
- **`compaction_score` sanitization depth** — Could not assess because: Sanitization logs missing. What data would have enabled it: Compactor step-by-step execution logs.

### 11D — Trace Structure Suggestions
1. **Most useful section:** `Deterministic Signals` auto-checker failures. Provides authoritative mechanical fault lines.
2. **Least useful section:** `Context Telemetry` token counts. Useful for bloat assessment but doesn't impact mechanical scoring.
3. **One piece of data to add:** `Compactor sanitization step logs`. Would enable accurate Section 5B scoring.
4. **Compaction signal reliability:** Reliable. Fired at T6 and T12 as expected.

## SECTION 12 — Actionable Issues

**Critical:**
- `- **Compaction sanitization entirely absent** (T6, T12) — Failure mode: `bad prompt`. Remediation: Update compactor system prompt to explicitly run `sanitize_quest_close`, `sanitize_condition`, `sanitize_pressure`, and `sanitize_inventory` steps after bullet generation.`
- `- **Progress extractor emits completed quests** (T2, T7) — Failure mode: `bad prompt`. Remediation: Add explicit `If a quest in active_quests already has status: completed, DO NOT emit it. Only emit active quests.``

**Major:**
- `- **State extractor zero-balance clamp fail** (T9) — Failure mode: `failed to output key information`. Remediation: Add explicit `If narration implies spending but inventory amount is 0, emit inventory_remove with amount 0 and flag as failed, or omit entirely.``
- `- **Scene extractor false npc_remove** (T7) — Failure mode: `bad prompt`. Remediation: Add explicit `Emit npc_remove ONLY when narration explicitly states departure, death, or removal. Absence ≠ departure.` with few-shot examples.`
- `- **Cross-prompt NPC/Quest duplication** (All turns) — Failure mode: `wasted tokens`. Remediation: Remove `present_npcs`, `active_quests`, and `recent_events` from Rules/State prompts. Pass via data flow only.`

**Minor:**
- `- **Pressure directive ignored** (T1, T8, T10, T12) — Failure mode: `bad prompt`. Remediation: Add explicit weaving instruction and few-shot example for pressure integration into narration.`
- `- **Fallback message leakage** (T9, T13) — Failure mode: `scope/domain mismatch`. Remediation: Fix system routing to strip fallback messages before LLM output.`