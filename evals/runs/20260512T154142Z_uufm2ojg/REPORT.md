# Eval Report — `full_cycle`

**Pack:** `eval-pack` · **Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8` · **Temp override:** `None`  
**Started:** 2026-05-12T15:41:42.705366+00:00 · **Finished:** 2026-05-12T15:49:15.522140+00:00  
**Output dir:** `/Users/pwilson/Repos/ccya/evals/runs/20260512T154142Z_uufm2ojg`  
**Compared against:** _(no prior run found)_

## Judge Summary

**Mechanical:** 3/5  
**Narrative:** 4/5  
**System Cohesion:** 3/5  
**Prompt Quality:** 4/5  
**Compaction:** 2/5  
**State Fidelity:** 69.0%  
**Prompt Adherence:** 92.0%
**Rubric:** `/Users/pwilson/Repos/ccya/evals/rubrics/default.md`
**Judge model:** `mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit`

**Pipeline scores:**
- rules: 4/5
- narrate: 4/5
- extract_scene: 3/5
- extract_state: 3/5
- extract_progress: 3/5

**Trace:** [`full_cycle.trace.md`](full_cycle.trace.md)
**Judge response:** [`full_cycle.judge.md`](full_cycle.judge.md)

## ⚠️  Flagged

### `rejected_deltas` — 2 rejected delta(s) across the run

- turn 9: 1 rejected
- turn 13: 1 rejected

## Other observations

- **`runner_errors`**: 2 turn(s) errored
- turn 9: engine_errors: [{"trace_id": "8d0f3cc1", "message": "Delta validation failed (1 rejection(s))."}]
- turn 13: engine_errors: [{"trace_id": "64c9e139", "message": "Delta validation failed (1 rejection(s))."}]


## Judge Verdict (full)

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

## Auto-Checker

**199 passed, 21 failed**

| Turn | Assertion | Result | Detail |
|---|---|---|---|
| 1 | `rules.rolled` | ❌ | rolled=True |
| 1 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=1 |
| 1 | `universal.pending_gm_beat.consumed` | ✅ | (first turn) |
| 1 | `universal.location_change.applied` | ✅ | (no change) |
| 1 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 1 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 1 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 1 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 1 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 1 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 1 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 1 | `universal.inventory.no_overdraw` | ✅ | (first turn) |
| 1 | `universal.pressure.immediate_cap` | ✅ | 1 immediate |
| 1 | `universal.narrate.pressure_directive_rendered` | ❌ | 1 immediate pressures but no Pressure/Overwhelm directive in narrate user prompt |
| 1 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 1 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 2 | `rules.rolled` | ❌ | rolled=False |
| 2 | `extract.state.inventory_remove` | ✅ | inventory_remove[credits] amount=500 |
| 2 | `extract.progress.quest_updates` | ✅ | quest_updates[settle_the_debt] found |
| 2 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 2 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 2 | `universal.location_change.applied` | ✅ | (no change) |
| 2 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 2 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Slowly'] |
| 2 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 2 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 2 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 2 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 2 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 2 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 2 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 2 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 2 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 2 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 2 | `progress.quest_id_collision` | ❌ | quest_updates re-creates already-completed quest id='settle_the_debt' |
| 3 | `rules.rolled` | ✅ | rolled=True |
| 3 | `extract.progress.quest_updates` | ✅ | quest_updates[deliver_the_ledger] found |
| 3 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=3 |
| 3 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 3 | `universal.location_change.applied` | ✅ | marrows_crossing -> marrows_crossing_square |
| 3 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 3 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 3 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 3 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 3 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 3 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 3 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 3 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 3 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 3 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 3 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 3 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 4 | `rules.rolled` | ✅ | rolled=False |
| 4 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=4 |
| 4 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 4 | `universal.location_change.applied` | ✅ | marrows_crossing_square -> merchant_road_east |
| 4 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 4 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Marrow', 'Crossing', 'Crossed'] |
| 4 | `universal.recent_events.ring_bounded` | ✅ | 6 entries |
| 4 | `universal.scene.npc_cap` | ✅ | 0 NPCs |
| 4 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 4 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 4 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 4 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 4 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 4 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 4 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 4 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 5 | `rules.rolled` | ✅ | rolled=True |
| 5 | `extract.scene.scene_tags` | ❌ | scene_tags[combat] not found |
| 5 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=5 |
| 5 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 5 | `universal.location_change.applied` | ✅ | (no change) |
| 5 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 5 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 5 | `universal.recent_events.ring_bounded` | ✅ | 7 entries |
| 5 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 5 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 5 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 5 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 5 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 5 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 5 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 5 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 5 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 6 | `rules.rolled` | ✅ | rolled=True |
| 6 | `extract.state.inventory_remove` | ✅ | inventory_remove[credits] amount=200 |
| 6 | `extract.progress.quest_updates` | ✅ | quest_updates[clear_the_road_toughs] found |
| 6 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=6 |
| 6 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 6 | `universal.location_change.applied` | ✅ | (no change) |
| 6 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 6 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 6 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 6 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 6 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 6 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 6 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 6 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 6 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 6 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 6 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 6 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 7 | `extract.progress.quest_updates` | ✅ | quest_updates[deliver_the_ledger] found |
| 7 | `extract.progress.quest_status` | ❌ | quest[deliver_the_ledger].status='active' (expected 'completed') |
| 7 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=7 |
| 7 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 7 | `universal.location_change.applied` | ✅ | merchant_road_east -> crossed_keys_inn |
| 7 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 7 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Ledger', 'Inside'] |
| 7 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 7 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 7 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 7 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 7 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 7 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 7 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 7 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 7 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 7 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 7 | `progress.quest_id_collision` | ❌ | quest_updates re-creates already-completed quest id='deliver_the_ledger' |
| 8 | `rules.rolled` | ✅ | rolled=True |
| 8 | `extract.state.inventory_remove` | ❌ | inventory_remove[brass_key] not found |
| 8 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 8 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 8 | `universal.location_change.applied` | ✅ | crossed_keys_inn -> inn_storage_room |
| 8 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 8 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Outside'] |
| 8 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 8 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 8 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 8 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 8 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 8 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 8 | `universal.pressure.immediate_cap` | ✅ | 1 immediate |
| 8 | `universal.narrate.pressure_directive_rendered` | ❌ | 1 immediate pressures but no Pressure/Overwhelm directive in narrate user prompt |
| 8 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 8 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 9 | `rules.rolled` | ❌ | rolled=False |
| 9 | `extract.scene.scene_tags` | ❌ | scene_tags[social] not found |
| 9 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 9 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 9 | `universal.location_change.applied` | ✅ | (no change) |
| 9 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 9 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Beyond'] |
| 9 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 9 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 9 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 9 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 9 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 9 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 9 | `universal.pressure.immediate_cap` | ✅ | 2 immediate |
| 9 | `universal.narrate.pressure_directive_rendered` | ✅ | directive present |
| 9 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 9 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 10 | `rules.rolled` | ✅ | rolled=True |
| 10 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=10 |
| 10 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 10 | `universal.location_change.applied` | ✅ | inn_storage_room -> inn_common_room |
| 10 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 10 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 10 | `universal.recent_events.ring_bounded` | ✅ | 6 entries |
| 10 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 10 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 10 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 10 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 10 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 10 | `universal.pressure.immediate_cap` | ✅ | 2 immediate |
| 10 | `universal.narrate.pressure_directive_rendered` | ❌ | 2 immediate pressures but no Pressure/Overwhelm directive in narrate user prompt |
| 10 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 10 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 11 | `rules.rolled` | ✅ | rolled=True |
| 11 | `extract.scene.scene_tags` | ✅ | scene_tags[combat] found |
| 11 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=11 |
| 11 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 11 | `universal.location_change.applied` | ✅ | (no change) |
| 11 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 11 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 11 | `universal.recent_events.ring_bounded` | ✅ | 7 entries |
| 11 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 11 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 11 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 11 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 11 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 11 | `universal.pressure.immediate_cap` | ✅ | 3 immediate |
| 11 | `universal.narrate.pressure_directive_rendered` | ✅ | directive present |
| 11 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 11 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 12 | `rules.rolled` | ❌ | rolled=True |
| 12 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=12 |
| 12 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 12 | `universal.location_change.applied` | ✅ | inn_common_room -> river_docks |
| 12 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 12 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 12 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 12 | `universal.scene.npc_cap` | ✅ | 0 NPCs |
| 12 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 12 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 12 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 12 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 12 | `universal.pressure.immediate_cap` | ✅ | 2 immediate |
| 12 | `universal.narrate.pressure_directive_rendered` | ❌ | 2 immediate pressures but no Pressure/Overwhelm directive in narrate user prompt |
| 12 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 12 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 13 | `rules.rolled` | ✅ | rolled=False |
| 13 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 13 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 13 | `universal.location_change.applied` | ✅ | (no change) |
| 13 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 13 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 13 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 13 | `universal.scene.npc_cap` | ✅ | 0 NPCs |
| 13 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 13 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 13 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 13 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 13 | `universal.pressure.immediate_cap` | ✅ | 2 immediate |
| 13 | `universal.narrate.pressure_directive_rendered` | ✅ | directive present |
| 13 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 13 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |

## Universal Assert Results

| Assertion | Severity | Turns Failed | Turns Checked | First Failure Turn |
|---|---|---:|---:|---:|
| `extract.progress.quest_status` | 🔴 | 1 | 1 | T7 |
| `extract.progress.quest_updates` | 🔴 | 0 | 4 | — |
| `extract.scene.scene_tags` | 🔴 | 2 | 3 | T5 |
| `extract.state.inventory_remove` | 🔴 | 1 | 3 | T8 |
| `progress.quest_id_collision` | 🔴 | 2 | 2 | T2 |
| `rules.rolled` | 🔴 | 4 | 12 | T1 |
| `universal.inventory.no_overdraw` | 🔴 | 0 | 13 | — |
| `universal.location_change.applied` | 🔴 | 0 | 13 | — |
| `universal.momentum.band_delta` | 🔴 | 0 | 13 | — |
| `universal.narrate.binding_present` | 🔴 | 0 | 13 | — |
| `universal.narrate.pressure_directive_rendered` | 🔴 | 4 | 13 | T1 |
| `universal.npc_mention.extracted` | 🔴 | 7 | 13 | T2 |
| `universal.pacing.floor_no_relief` | 🟡 | 0 | 13 | — |
| `universal.pc.condition_no_dupes` | 🔴 | 0 | 13 | — |
| `universal.pending_gm_beat.consumed` | 🔴 | 0 | 13 | — |
| `universal.pressure.immediate_cap` | 🔴 | 0 | 13 | — |
| `universal.pressure.no_stale_immediate` | 🟡 | 0 | 13 | — |
| `universal.progress.actions_quality` | 🔴 | 0 | 13 | — |
| `universal.recent_events.ring_bounded` | 🔴 | 0 | 13 | — |
| `universal.recent_events_add.turn_stamped` | 🔴 | 0 | 13 | — |
| `universal.scene.npc_cap` | 🔴 | 0 | 13 | — |

## Pacing Metrics

### Pressure Duration

| Pressure ID | First Turn | Last Turn | Duration (turns) | Flagged |
|---|---|---:|---:|---|
| `caron_impatience` | T1 | T1 | 1 |  |
| `inn_brawl_chaos` | T11 | T11 | 1 |  |
| `road_ambush_threat` | T4 | T13 | 10 | ⚠️ >8 turns |
| `road_surveillance` | T3 | T13 | 11 | ⚠️ >8 turns |
| `storage_room_confinement` | T8 | T9 | 2 |  |

### Location Dwell

| Location ID | Turns Active | Flagged |
|---|---:|---|
| `crossed_keys_inn` | 1 |  |
| `inn_common_room` | 2 |  |
| `inn_storage_room` | 2 |  |
| `marrows_crossing` | 2 |  |
| `marrows_crossing_square` | 1 |  |
| `merchant_road_east` | 3 |  |
| `river_docks` | 2 |  |

### Condition Duration

| Condition ID | First Turn | Last Turn | Duration (turns) | Flagged |
|---|---|---:|---:|---|
| `bruised_ribs` | T1 | T13 | 13 | ⚠️ >6 turns |
| `low_morale` | T1 | T1 | 1 |  |

## Turn Metrics

| # | input | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | retries | parse_fail | duration_s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | Walk over to Caron's table and sit down across f… | 1403 | 3255 | 2759 | 3423 | 4370 | 0 | 0 | 36.21 |
| 2 | I slide 500 credits across the table to Caron an… | 1721 | 3417 | 3100 | 3504 | 4684 | 0 | 0 | 29.24 |
| 3 | I find Halden by the town well and offer to carr… | 1802 | 3852 | 3164 | 3437 | 4736 | 0 | 0 | 32.62 |
| 4 | I leave Marrow's Crossing by the east gate and h… | 1733 | 4059 | 2964 | 3395 | 4509 | 0 | 0 | 30.02 |
| 5 | I walk up to the two toughs at the inn door and … | 1639 | 4159 | 2983 | 3565 | 4722 | 0 | 0 | 37.89 |
| 6 | I drop 200 credits on the ground between the tou… | 1880 | 4350 | 3214 | 3477 | 4891 | 0 | 0 | 47.05 |
| 7 | I sit across from Halden at his table, slide the… | 1788 | 4364 | 3167 | 3488 | 4730 | 0 | 0 | 35.52 |
| 8 | I pull out the brass key Halden gave me and try … | 1777 | 4460 | 2992 | 3334 | 4579 | 0 | 0 | 28.97 |
| 9 | I press my ear against the inn's stone wall and … | 1645 | 4122 | 2925 | 3429 | 4481 | 0 | 0 | 31.73 |
| 10 | I approach Matthew Estrada at the bar, grab his … | 1745 | 4336 | 3068 | 3471 | 4737 | 0 | 0 | 34.86 |
| 11 | Matthew's bodyguard draws a knife! I tackle him … | 1830 | 4364 | 3190 | 3401 | 4777 | 0 | 0 | 33.06 |
| 12 | I grab the ledger from my coat and sprint out th… | 1738 | 4447 | 3062 | 3362 | 4792 | 0 | 0 | 44.51 |
| 13 | I find a quiet corner at the dock and wrap my wo… | 1621 | 4317 | 2865 | 3490 | 4423 | 0 | 0 | 31.03 |
|  | TOTALS | 22322 | 53502 | 39453 | 44776 | 60431 | 0 | 0 | 452.73 |

**Total turns:** 13 · **Total duration:** 452.73s · **Avg/turn:** 34.83s
**Total tokens in:** 220,484 · **Total tokens out:** 14,401 · **Total LLM time:** 428.4s
**Total retries:** 0 · **Total parse failures:** 0

