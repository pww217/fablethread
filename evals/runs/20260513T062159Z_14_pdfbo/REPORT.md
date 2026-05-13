# Eval Report — `full_cycle`

**Pack:** `eval-pack` · **Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8` · **Temp override:** `None`  
**Started:** 2026-05-13T06:21:59.564503+00:00 · **Finished:** 2026-05-13T07:10:52.445862+00:00  
**Output dir:** `/Users/pwilson/Repos/ccya/evals/runs/20260513T062159Z_14_pdfbo`  
**Compared against:** `/Users/pwilson/Repos/ccya/evals/runs/20260513T021317Z_pys5ya6s/artifacts`

## Judge Summary

**Mechanical:** 4/5  
**Narrative:** 4/5  
**System Cohesion:** 4/5  
**Prompt Quality:** 4/5  
**Compaction:** 4/5  
**State Fidelity:** 85.0%  
**Prompt Adherence:** 92.0%
**Rubric:** `/Users/pwilson/Repos/ccya/evals/rubrics/default.md`
**Judge model:** `mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit`

**Pipeline scores:**
- rules: 5/5
- narrate: 4/5
- extract_scene: 5/5
- extract_state: 5/5
- extract_progress: 3/5

**Trace:** [`full_cycle.trace.md`](full_cycle.trace.md)
**Judge response:** [`full_cycle.judge.md`](full_cycle.judge.md)

## ✅ No flags

No regressions, retries, failures, or judge score drops detected.


## Judge Verdict (full)

# SECTION 1 — Mechanic Lifecycle Tables

### 1A — Momentum Table
| Turn | Roll Band | Δ Momentum | Band Before→After | Tone Match? | Flag |
|------|-----------|------------|-------------------|-------------|------|
| 1 | — | 0 | 0→0 | — | — |
| 2 | — | 0 | 0→0 | — | — |
| 3 | — | 0 | 0→0 | — | — |
| 4 | — | 0 | 0→0 | — | — |
| 5 | crit_success | +2 | 0→2 | Yes | — |
| 6 | crit_success | +1 | 2→3 | Yes | — |
| 7 | — | 0 | 3→3 | — | — |
| 8 | crit_success | 0 | 3→3 | Yes | FLAT |
| 9 | — | 0 | 3→3 | — | — |
| 10 | success | 0 | 3→3 | Yes | FLAT |
| 11 | partial | 0 | 3→3 | Yes | FLAT |
| 12 | crit_success | 0 | 3→3 | Yes | FLAT |
| 13 | — | 0 | 3→3 | — | — |

Momentum responds correctly to dice but hits the `momentum_max: 3` cap at T6 and stays there. This is mechanically correct per constants, though it reduces mechanical variance in late turns.

### 1B — GM Beat Table
| Generated (Tn) | Beat Type | Surfaced (Tm) | Surface Lag (turns) | Effect | Flag |
|----------------|-----------|---------------|---------------------|--------|------|
| 5 | pressure | 6 | 1 | Scarred Tough steps closer | — |
| 7 | pressure | 8 | 1 | Traveler collapses | — |
| 9 | pressure | 10 | 1 | Traveler convulses | — |
| 11 | escalation | 12 | 1 | Matthew recovers | — |
| 13 | pressure | 14 | 1 | River current treacherous | — |

Beats generate at appropriate frequency (every 2 turns). Types vary (pressure/escalation). Surface lag is consistently 1 turn. No orphans or lags.

### 1C — Scene Pressure Table
| ID | Added (Tn) | Urgency | Escalated? | Resolved (Tm) | Lifespan (turns) | Flag |
|----|------------|---------|------------|---------------|-----------------|------|
| scarred_tough_threat | — | — | — | 6 | 1 | UNRESOLVED_AT_END |

Only one pressure removal is recorded at T6. No pressures were added in the trace, so lifecycle tracking is minimal. The removal at T6 implies a pressure existed off-trace or was beat-derived. No pacing-flat turns observed.

### 1D — Condition Lifecycle Table
| ID | Added (Tn) | Source | Still Present (Tm) | Resolved | Duration (turns) | Flag |
|----|------------|--------|--------------------|----------|-----------------|------|
| bruised_ribs | 0 (seed) | engine | 12 | 13 | 13 | OVERLONG |
| low_morale | 0 (seed) | engine | 13 | — | 13 | — |

`bruised_ribs` persisted for 13 turns before narrative resolution at T13. Flagged `OVERLONG`. `low_morale` persists as intended.

### 1E — Quest Arc Table
| Quest ID | Created (Tn) | Objectives | Objectives Done | Resolved (Tm) | Outcome | Flag |
|----------|--------------|------------|-----------------|---------------|---------|------|
| settle_the_debt | 0 (seed) | 2 | 2 | 2 | completed | — |
| clear_the_road_toughs | 0 (seed) | 2 | 2 | 6 | completed | — |
| deliver_the_ledger | 0 (seed) | 3 | 3 | 7 | completed | — |
| deliver_halden_ledger | 8 | 0 | 1 | — | active | ORPHANED |
| warn_caron | 13 | 1 | 0 | — | active | — |

`deliver_halden_ledger` was created at T8 with an empty objectives array. State shows `objectives: []` at T12 despite obj 1 being marked done. This is a state drift/extraction failure.

### 1F — Inventory Evolution Table
| Turn | Action | Item | Qty | Narration Reflected? | Extracted? | Flag |
|------|--------|------|-----|---------------------|------------|------|
| 2 | remove | credits | 50 | Yes (narration says 50) | Yes | AMOUNT_MISMATCH |
| 3 | add | leather_bound_ledger | 1 | Yes | Yes | — |
| 7 | remove | leather_bound_ledger | 1 | Yes | Yes | — |
| 8 | remove | brass_key | 1 | Yes | Yes | — |
| 9 | remove | credits | 1 | Yes | Yes | — |
| 11 | add | brass_key | 1 | Yes (metallic object) | Yes | — |
| 12 | add | halden_ledger | 1 | Yes | Yes | — |
| 13 | remove | credits | 1 | Yes | Yes | — |

T2 shows `AMOUNT_MISMATCH`: player said 500, narration said 50, state removed 50. Extraction matched narration, not player intent.

---

# SECTION 2 — State Fidelity

### 2A — State Coherence
State evolves logically across turns. Inventory tracks credits, ledger, and key accurately. Quests advance in sequence. Conditions resolve when narratively appropriate. The only coherence break is `deliver_halden_ledger` at T8/T12, where the quest object array is empty despite objectives being marked done, indicating a structural drift in the progress extractor's quest serialization.

### 2B — State Drift
- **T2 Narration Drift:** Player input: "slide 500 credits". Narration: "sliding the fifty coins". State extractor removed 50. This contradicts the "Player input is truth" rule.
- **T8 Quest Drift:** Progress extractor created `deliver_halden_ledger` with `objectives: []`. State reflects empty array. This breaks quest tracking integrity.
- **T11 Item Inference:** Narration says "cold, hard shape of something metallic". State extractor names it `brass_key`. Plausible given context (Halden's key), but technically an assumption not explicitly confirmed in narration.

### 2C — State Completeness
All domains updated correctly. Progress extractor failed to populate `deliver_halden_ledger` objectives. Scene extractor correctly tracked NPC additions/removals. State extractor correctly handled inventory and condition lifecycles.

### 2D — State Fidelity Rate Calculation
Turns with no rejected deltas and no detected drift: 1, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13 = 11 turns.
Drift turns: 2 (narration), 8 (quest structure).
Calculation: 11 / 13 = 0.846 → **0.85**

---

# SECTION 3 — Prompt Quality Audit

### 3A — Rules Pipeline Prompt Audit
| Criterion | Score | Evidence |
|-----------|-------|----------|
| P1 | Y | System static, user turn-variable. |
| P2 | Y | Matches architecture diagram. |
| P3 | Y | No cross-pipeline duplication. |
| P4 | Y | Schema vs guidance clearly separated. |
| P5 | Y | No contradictions. |
| P6 | Y | Terse, directive-focused. |
| P7 | Y | JSON schema concrete, priority rules numbered. |
| P8 | Y | Outputs comply with rules. |
| P9 | N | Failure modes rare; few-shot not needed. |

**Remediation summary:** None. Rules prompt is well-architected.

### 3B — Narrate Pipeline Prompt Audit
| Criterion | Score | Evidence |
|-----------|-------|----------|
| P1 | Y | System static, user turn-variable. |
| P2 | Y | Matches architecture diagram. |
| P3 | Y | No cross-pipeline duplication. |
| P4 | Y | Schema vs guidance separated. |
| P5 | Y | No contradictions. |
| P6 | Y | Terse, directive-focused. |
| P7 | Y | JSON schema concrete, priority rules numbered. |
| P8 | N | T2 violated "Player input is truth" (50 vs 500). |
| P9 | N | Failure modes rare; few-shot not needed. |

**Remediation summary:** 
- **Issue:** T2 narration contradicted player input amount.
- **Change:** Strengthen "Player input is truth" rule with explicit negative constraint: "NEVER alter explicit numerical values from player input unless the rules outcome dictates a cost."
- **Outcome:** Prevents narration drift on transactional inputs.

### 3C — Extract Scene Prompt Audit
| Criterion | Score | Evidence |
|-----------|-------|----------|
| P1 | Y | System static, user turn-variable. |
| P2 | Y | Matches architecture diagram. |
| P3 | Y | No cross-pipeline duplication. |
| P4 | Y | Schema vs guidance separated. |
| P5 | Y | No contradictions. |
| P6 | Y | Terse, directive-focused. |
| P7 | Y | JSON schema concrete, priority rules numbered. |
| P8 | Y | Outputs comply with rules. |
| P9 | N | Failure modes rare; few-shot not needed. |

**Remediation summary:** None. Scene prompt is robust.

### 3D — Extract State Prompt Audit
| Criterion | Score | Evidence |
|-----------|-------|----------|
| P1 | Y | System static, user turn-variable. |
| P2 | Y | Matches architecture diagram. |
| P3 | Y | No cross-pipeline duplication. |
| P4 | Y | Schema vs guidance separated. |
| P5 | Y | No contradictions. |
| P6 | Y | Terse, directive-focused. |
| P7 | Y | JSON schema concrete, priority rules numbered. |
| P8 | Y | Outputs comply with rules. |
| P9 | N | Failure modes rare; few-shot not needed. |

**Remediation summary:** None. State prompt is robust.

### 3E — Extract Progress Prompt Audit
| Criterion | Score | Evidence |
|-----------|-------|----------|
| P1 | Y | System static, user turn-variable. |
| P2 | Y | Matches architecture diagram. |
| P3 | Y | No cross-pipeline duplication. |
| P4 | Y | Schema vs guidance separated. |
| P5 | Y | No contradictions. |
| P6 | Y | Terse, directive-focused. |
| P7 | Y | JSON schema concrete, priority rules numbered. |
| P8 | N | T2, T6, T7 violated quest dedup rule. T8 created empty quest. |
| P9 | Y | T2/T6/T7 failures are example-preventable. |

**Remediation summary:**
- **Issue:** Progress extractor re-emits completed quests (T2, T6, T7) and creates quests with empty objectives (T8).
- **Change:** Add explicit few-shot examples showing `NEVER emit quest_updates if status=completed` and `NEVER emit quest_updates with empty objectives array; always populate from active_quests list`.
- **Outcome:** Eliminates quest dedup collisions and structural drift.

### 3F — Prompt Adherence Rate Calculation
Total instances: 5 pipelines × 13 turns = 65.
Failures: Narrate T2 (1), Progress T2/T6/T7 (3), Progress T8 (1) = 5.
Pass instances: 60.
Rate: 60 / 65 = 0.923 → **0.92**

### 3G — Cross-Pipeline Redundancy Summary
- **narrate + scene:** Seed state location description duplicated. Intentional (scene needs location context).
- **narrate + progress:** World state bullets duplicated. Intentional (progress needs world context).
- **Estimated token waste:** ~120 tokens/turn. Negligible.
- **Top 3 dedup opportunities:** None. Redundancy is architectural and justified.

---

# SECTION 4 — Mechanic Interplay Assessment

### 4A — Beat→Narrative Loop
Tight. Beats are generated, surfaced within 1 turn, and integrated into narration. Disposition logic (consume/replace) works correctly. No orphans.

### 4B — Momentum→Directive→Tone Chain
Tight. Momentum caps at 3, tone remains urgent/tense. Directives (Location Pressure, Location Imperative) honored in narration. No breaks.

### 4C — Pressure→Stakes→Consequence Chain
Loose. Only one pressure removal recorded. Pressures are beat-derived rather than explicitly added/updated. Stakes naming in rules is generic. Consequences are narratively handled but mechanically light.

### 4D — Condition→Narrative Callback
Tight. `bruised_ribs` referenced in narration every 2-3 turns. Resolved at T13 when player wraps wounds. `low_morale` persists as intended.

### 4E — Pacing Assessment
High-tension throughout. Location pressure directives at T7/T10 prevent stagnation. Momentum arc: 0 → 2 → 3 (peak) → sustained. Beat type variety: pressure/escalation. Escape paths: T11 partial roll led to finding key, T12 crit success led to escape. No death spirals.

### 4F — NPC Entry/Exit Coherence
Tight. Halden leaves T7. Toughs leave T6. Matthew enters T10. Jace enters T13. All tracked in `present_npcs` and compendium. No ghost NPCs.

### 4G — Player Intent Fidelity
Tight, except T2. T2 narration altered 500 to 50. T9 absurd input (bribe wall) handled pragmatically. T11 tackle handled correctly. T12 escape handled correctly. T13 repair handled correctly.

### 4H — GM Beat Lifecycle
Tight. Beats cycle correctly. TTL respected. Disposition honored. No orphaned beats.

---

# SECTION 5 — Compaction Report

### 5A — Chronicle Quality
T6 bullets: Accurate. Covers T1-T3. Named entities preserved.
T12 bullets: Accurate. Covers T4-T9. Named entities preserved.
No generic or inverted bullets.
Score: `[OK]`

### 5B — Sanitization Fidelity
T6: `quest_close`: NA. `condition_remove`: NA. `pressure_remove`: NA. `inventory_remove`: NA. `recent_events_compact`: OK.
T12: `quest_close`: NA. `condition_remove`: NA. `pressure_remove`: NA. `inventory_remove`: NA. `recent_events_compact`: OK.
Sanitization actions recorded as empty in trace. Assuming compactor ran but logged nothing, or sanitization is implicit.
Score: `[OK]`

### 5C — Compaction Score
Bullets accurate. Sanitization implicit/OK.
Score: **4/5**

---

# SECTION 6 — Auto-Checker Failures

1. `universal.npc_mention.extracted` (T1, T3, T4, T5, T7, T11, T13): Narration mentions capitalized words ("Crossed", "Inside", "Master", "Leather", "Shelf") flagged as untracked NPCs. **False positive.** Checker is over-matching capitalized nouns. Recommend regex fix to exclude common nouns/location fragments.
2. `progress.quest_id_collision` (T2, T6, T7): Progress extractor re-emits completed quests. **True failure.** Violates "NEVER emit a completed quest again" rule. Remediation: Add explicit pre-check in progress prompt: "If quest status=completed, omit entirely."
3. T8 `deliver_halden_ledger` empty objectives: Not in auto-checker but noted. **True failure.** Remediation: Add few-shot showing quest creation with populated objectives.

---

# SECTION 7 — Per-Pipeline Mechanical Critique

### Rules
**What Went Well:** T5/T6/T8/T10/T11/T12 rolls correctly classified intent, skill, and difficulty. Stakes naming consistent.
**What Went Poorly:** None.
**Prompt Adherence Failures:** None this run.
**Mechanic Ownership Check:** Correct.
**Scope Discipline:** Correct.
**Issues Bulleted List:** None.
**Pipeline Score:** 5/5

### Narrate
**What Went Well:** T9 handles absurd input pragmatically. T11/T12 combat/escape prose is tight.
**What Went Poorly:** T2 narration says "fifty coins" instead of 500. Violates "Player input is truth".
**Prompt Adherence Failures:** T2: "Player input is truth" rule violated.
**Mechanic Ownership Check:** Correct.
**Scope Discipline:** Correct.
**Issues Bulleted List:** `- **Narration drift on transactional amounts** (turns: 2) — Failure mode: failed to input key information. Remediation: Strengthen "Player input is truth" rule with explicit negative constraint against altering numerical values.`
**Pipeline Score:** 4/5

### Extract Scene
**What Went Well:** T3/T7/T12 location changes tracked accurately. T13 NPC addition (Jace) correct.
**What Went Poorly:** None.
**Prompt Adherence Failures:** None this run.
**Mechanic Ownership Check:** Correct.
**Scope Discipline:** Correct.
**Issues Bulleted List:** None.
**Pipeline Score:** 5/5

### Extract State
**What Went Well:** T2/T6/T9/T13 inventory removals accurate. T13 condition removal accurate.
**What Went Poorly:** None.
**Prompt Adherence Failures:** None this run.
**Mechanic Ownership Check:** Correct.
**Scope Discipline:** Correct.
**Issues Bulleted List:** None.
**Pipeline Score:** 5/5

### Extract Progress
**What Went Well:** T5/T6/T7 quest objective completion tracked. T13 new quest creation correct.
**What Went Poorly:** T2/T6/T7 re-emit completed quests. T8 creates quest with empty objectives.
**Prompt Adherence Failures:** T2, T6, T7: "NEVER emit a completed quest again" rule violated. T8: Quest schema rule violated (empty objectives).
**Mechanic Ownership Check:** Correct.
**Scope Discipline:** Correct.
**Issues Bulleted List:** `- **Quest dedup failure** (turns: 2, 6, 7) — Failure mode: failed to output key information. Remediation: Add explicit pre-check rule: "If quest status=completed, omit from quest_updates entirely."`
`- **Empty quest objectives** (turns: 8) — Failure mode: schema drift. Remediation: Add few-shot showing quest creation with populated objectives array.`
**Pipeline Score:** 3/5 (Major failures cap at 3)

---

# SECTION 8 — Cross-Pipeline Correlation

### Rules → Narrate Binding
Tight. Roll bands shape narration weight. T5/T6 crit successes lead to favorable outcomes. T11 partial leads to complication.

### Rules → Extract State Routing
T2/T6/T9/T13 stakes correctly named. Consequences extracted accurately.

### Narrate → Scene Extract Consistency
T3/T7/T12 location changes narrated → scene extract captures them. T13 NPC addition narrated → scene extract captures it.

### Narrate → State Extract Consistency
T2/T6/T9/T13 inventory changes narrated → state extract captures them. T13 condition change narrated → state extract captures it.

### Narrate → Progress Extract Consistency
T5/T6/T7 quest objectives narrated → progress extract captures them. T13 quest creation narrated → progress extract captures it.

### Progress → Narrate Feedback Loop
T5/T7/T9/T11/T13 beats surfaced in narration T+(N+1). Recent events appear in context. Pressures feed rules context.

---

# SECTION 9 — Storytelling Criteria (SECONDARY)

### quest_arc_quality
Quests form a compelling arc. `settle_the_debt`, `clear_the_road_toughs`, `deliver_the_ledger` completed sequentially. `warn_caron` emerges naturally. Completion feels earned.

### rewards_and_consequences
Successes (T5, T6, T8, T12) produce positive outcomes (toughs leave, key found, escape). Failures/Partials (T11) produce complications (tackle, search) but not dead ends.

### world_consistency
All entities sanctioned. Jace Miller introduced plausibly. Matthew Estrada tracked. No unsanctioned introductions.

### failure_arc
T11 partial roll leads to finding key, T12 escape. T2 narration drift is a mechanical failure, not narrative. Failures create interesting options.

---

# SECTION 10 — Verdicts

### V1 — Mechanical Integrity → 4
Strong extraction across scene/state. Progress pipeline has consistent quest dedup failures (T2, T6, T7) and structural drift (T8 empty objectives). Rules and narration are solid.

### V2 — Narrative Quality → 4
Prose is tight, handles absurd input well, respects dice bands. T2 narration drift is a notable flaw.

### V3 — System Cohesion → 4
Pipelines communicate well. Beat lifecycle works. Quest state drift at T8 is the main cohesion break.

### V4 — Prompt Quality → 4
Adherence is high (0.92). Progress prompt needs few-shot examples for quest dedup and objective population.

### V5 — Compaction → 4
Chronicle bullets accurate. Sanitization implicit but effective.

---

# SECTION 11 — Trace Quality and Eval Self-Assessment

### 11A — Input Sufficiency
| Data Category | Rating | Notes |
|---|---|---|
| System prompts (all 5 pipelines) | SUFFICIENT | Complete and readable. |
| Per-turn user prompts (all 5 pipelines) | SUFFICIENT | Fully visible. |
| Per-turn engine outputs (rules, narrate, extractors) | SUFFICIENT | Complete. |
| State snapshots (per turn) | SUFFICIENT | Full snapshots/diffs sufficient. |
| Applied/rejected deltas | SUFFICIENT | Detailed enough. |
| Context telemetry (token counts, trim status) | SUFFICIENT | Sufficient. |
| Static context (pack style, seed state, engine constants) | SUFFICIENT | Complete. |
| Compaction signals | SUFFICIENT | Correctly identified. |
| Auto-checker signals | SUFFICIENT | Clearly attributed. |

### 11B — Missing Data
None.

### 11C — Questions You Could Not Answer
None.

### 11D — Trace Structure Suggestions
1. Most useful: State diffs (clear drift detection).
2. Least useful: Redundant world state blocks (justified but verbose).
3. Best addition: Explicit compaction sanitization logs (currently empty).
4. Compaction signal reliable: Yes.

---

# SECTION 12 — Actionable Issues

**Critical:**
- **Quest dedup failure** (turns: 2, 6, 7) — Failure mode: failed to output key information. Remediation: Add explicit pre-check rule in progress prompt: "If quest status=completed, omit from quest_updates entirely. Do not re-emit."

**Major:**
- **Narration drift on transactional amounts** (turns: 2) — Failure mode: failed to input key information. Remediation: Strengthen "Player input is truth" rule with explicit negative constraint: "NEVER alter explicit numerical values from player input unless the rules outcome dictates a cost."
- **Empty quest objectives on creation** (turns: 8) — Failure mode: schema drift. Remediation: Add few-shot examples showing quest creation with populated objectives array derived from `active_quests` or player intent.

**Minor:**
- **Momentum flatlining at cap** (turns: 8-13) — Failure mode: mechanical variance loss. Remediation: Consider soft cap or momentum decay mechanic to restore variance in late turns.
- **Auto-checker false positives on capitalized nouns** (turns: 1, 3, 4, 5, 7, 11, 13) — Failure mode: scope/domain mismatch. Remediation: Update regex to exclude common nouns/location fragments from NPC mention checks.

## Auto-Checker

**241 passed, 19 failed**

| Turn | Assertion | Result | Detail |
|---|---|---|---|
| 1 | `rules.rolled` | ✅ | rolled=False |
| 1 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 1 | `universal.pending_gm_beat.consumed` | ✅ | (first turn) |
| 1 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 1 | `universal.location_change.applied` | ✅ | (no change) |
| 1 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 1 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed', 'Inside'] |
| 1 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 1 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 1 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 1 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 1 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 1 | `universal.inventory.no_overdraw` | ✅ | (first turn) |
| 1 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 1 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 1 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 1 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 1 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 1 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 2 | `rules.rolled` | ❌ | rolled=False |
| 2 | `extract.state.inventory_remove` | ❌ | inventory_remove[credits] amount=50 |
| 2 | `extract.progress.quest_updates` | ✅ | quest_updates[settle_the_debt] found |
| 2 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 2 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 2 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 2 | `universal.location_change.applied` | ✅ | (no change) |
| 2 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 2 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 2 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 2 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 2 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 2 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 2 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 2 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 2 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 2 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 2 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 2 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 2 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 2 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 2 | `progress.quest_id_collision` | ❌ | quest_updates re-creates already-completed quest id='settle_the_debt' |
| 3 | `rules.rolled` | ❌ | rolled=False |
| 3 | `extract.progress.quest_updates` | ✅ | quest_updates[deliver_the_ledger] found |
| 3 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=3 |
| 3 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 3 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 3 | `universal.location_change.applied` | ✅ | marrows_crossing -> marrows_crossing_square |
| 3 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 3 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 3 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 3 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 3 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 3 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 3 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 3 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 3 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 3 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 3 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 3 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 3 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 3 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 4 | `rules.rolled` | ✅ | rolled=False |
| 4 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 4 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 4 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 4 | `universal.location_change.applied` | ✅ | marrows_crossing_square -> marrow_crossing_outskirts |
| 4 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 4 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 4 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 4 | `universal.scene.npc_cap` | ✅ | 0 NPCs |
| 4 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 4 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 4 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 4 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 4 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 4 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 4 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 4 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 4 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 4 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 5 | `rules.rolled` | ✅ | rolled=True |
| 5 | `extract.scene.scene_tags` | ❌ | scene_tags[standoff] not found |
| 5 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=5 |
| 5 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 5 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 5 | `universal.location_change.applied` | ✅ | (no change) |
| 5 | `universal.narrate.binding_present` | ✅ | no roll required, binding not expected |
| 5 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Before', 'Crossed', 'Master'] |
| 5 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 5 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 5 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 5 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 5 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 5 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 5 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 5 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 5 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 5 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 5 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 5 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 6 | `rules.rolled` | ✅ | rolled=True |
| 6 | `extract.state.inventory_remove` | ✅ | inventory_remove[credits] amount=200 |
| 6 | `extract.progress.quest_updates` | ✅ | quest_updates[clear_the_road_toughs] found |
| 6 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=6 |
| 6 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 6 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 6 | `universal.location_change.applied` | ✅ | (no change) |
| 6 | `universal.narrate.binding_present` | ✅ | no roll required, binding not expected |
| 6 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 6 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 6 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 6 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 6 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 6 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 6 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 6 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 6 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 6 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 6 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 6 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 6 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 6 | `progress.quest_id_collision` | ❌ | quest_updates re-creates already-completed quest id='clear_the_road_toughs' |
| 7 | `extract.progress.quest_updates` | ✅ | quest_updates[deliver_the_ledger] found |
| 7 | `extract.progress.quest_status` | ❌ | quest[deliver_the_ledger].status='active' (expected 'completed') |
| 7 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=7 |
| 7 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 7 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 7 | `universal.location_change.applied` | ✅ | marrow_crossing_outskirts -> crossed_keys_inn |
| 7 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 7 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Leather'] |
| 7 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 7 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 7 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 7 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 7 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 7 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 7 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 7 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 7 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 7 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 7 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 7 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 7 | `progress.quest_id_collision` | ❌ | quest_updates re-creates already-completed quest id='deliver_the_ledger' |
| 8 | `rules.rolled` | ✅ | rolled=True |
| 8 | `extract.state.inventory_remove` | ❌ | inventory_remove[brass_key] amount=0 |
| 8 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=8 |
| 8 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 8 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 8 | `universal.location_change.applied` | ✅ | (no change) |
| 8 | `universal.narrate.binding_present` | ✅ | no roll required, binding not expected |
| 8 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 8 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 8 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 8 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 8 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 8 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 8 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 8 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 8 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 8 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 8 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 8 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 8 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 9 | `rules.rolled` | ❌ | rolled=False |
| 9 | `extract.scene.scene_tags` | ❌ | scene_tags[social] not found |
| 9 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 9 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 9 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 9 | `universal.location_change.applied` | ✅ | (no change) |
| 9 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 9 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 9 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 9 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 9 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 9 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 9 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 9 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 9 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 9 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 9 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 9 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 9 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 9 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 10 | `rules.rolled` | ✅ | rolled=True |
| 10 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=10 |
| 10 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 10 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 10 | `universal.location_change.applied` | ✅ | (no change) |
| 10 | `universal.narrate.binding_present` | ✅ | no roll required, binding not expected |
| 10 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 10 | `universal.recent_events.ring_bounded` | ✅ | 6 entries |
| 10 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 10 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 10 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 10 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 10 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 10 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 10 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 10 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 10 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 10 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 10 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 11 | `rules.rolled` | ✅ | rolled=True |
| 11 | `extract.scene.scene_tags` | ✅ | scene_tags[combat] found |
| 11 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=11 |
| 11 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 11 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 11 | `universal.location_change.applied` | ✅ | (no change) |
| 11 | `universal.narrate.binding_present` | ✅ | no roll required, binding not expected |
| 11 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Shelf'] |
| 11 | `universal.recent_events.ring_bounded` | ✅ | 7 entries |
| 11 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 11 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 11 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 11 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 11 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 11 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 11 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 11 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 11 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 11 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 11 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 12 | `rules.rolled` | ❌ | rolled=True |
| 12 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=12 |
| 12 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 12 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 12 | `universal.location_change.applied` | ✅ | crossed_keys_inn -> river_docks |
| 12 | `universal.narrate.binding_present` | ✅ | no roll required, binding not expected |
| 12 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 12 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 12 | `universal.scene.npc_cap` | ✅ | 0 NPCs |
| 12 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 12 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 12 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 12 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 12 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 12 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 12 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 12 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 12 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 12 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 13 | `rules.rolled` | ✅ | rolled=False |
| 13 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=13 |
| 13 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 13 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 13 | `universal.location_change.applied` | ✅ | (no change) |
| 13 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 13 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 13 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 13 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 13 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 13 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 13 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 13 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 13 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 13 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 13 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 13 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 13 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 13 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |

## Universal Assert Results

| Assertion | Severity | Turns Failed | Turns Checked | First Failure Turn |
|---|---|---:|---:|---:|
| `extract.progress.quest_status` | 🔴 | 1 | 1 | T7 |
| `extract.progress.quest_updates` | 🔴 | 0 | 4 | — |
| `extract.scene.scene_tags` | 🔴 | 2 | 3 | T5 |
| `extract.state.inventory_remove` | 🔴 | 2 | 3 | T2 |
| `progress.quest_id_collision` | 🔴 | 3 | 3 | T2 |
| `rules.rolled` | 🔴 | 4 | 12 | T2 |
| `universal.inventory.key_consumed` | 🟡 | 0 | 13 | — |
| `universal.inventory.no_negative_amount` | 🔴 | 0 | 13 | — |
| `universal.inventory.no_overdraw` | 🔴 | 0 | 13 | — |
| `universal.location_change.applied` | 🔴 | 0 | 13 | — |
| `universal.momentum.band_delta` | 🔴 | 0 | 13 | — |
| `universal.narrate.binding_present` | 🔴 | 0 | 13 | — |
| `universal.narrate.pressure_directive_rendered` | 🔴 | 0 | 13 | — |
| `universal.npc_mention.extracted` | 🔴 | 7 | 13 | T1 |
| `universal.pacing.floor_no_relief` | 🟡 | 0 | 13 | — |
| `universal.pc.condition_no_dupes` | 🔴 | 0 | 13 | — |
| `universal.pending_gm_beat.consumed` | 🔴 | 0 | 13 | — |
| `universal.pending_gm_beat.disposition_respected` | 🔴 | 0 | 13 | — |
| `universal.pressure.immediate_cap` | 🔴 | 0 | 13 | — |
| `universal.pressure.no_stale_immediate` | 🟡 | 0 | 13 | — |
| `universal.progress.actions_quality` | 🔴 | 0 | 13 | — |
| `universal.recent_events.ring_bounded` | 🔴 | 0 | 13 | — |
| `universal.recent_events_add.turn_stamped` | 🔴 | 0 | 13 | — |
| `universal.scene.npc_cap` | 🔴 | 0 | 13 | — |

## Pacing Metrics

### Location Dwell

| Location ID | Turns Active | Flagged |
|---|---:|---|
| `crossed_keys_inn` | 5 | ⚠️ >4 turns |
| `marrow_crossing_outskirts` | 3 |  |
| `marrows_crossing` | 2 |  |
| `marrows_crossing_square` | 1 |  |
| `river_docks` | 2 |  |

### Condition Duration

| Condition ID | First Turn | Last Turn | Duration (turns) | Flagged |
|---|---|---:|---:|---|
| `bruised_ribs` | T1 | T12 | 12 | ⚠️ >6 turns |
| `low_morale` | T1 | T13 | 13 | ⚠️ >6 turns |

## Turn Metrics

| # | input | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | retries | parse_fail | duration_s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | Walk over to Caron's table and sit down across f… | 1583 (+0) | 3527 (+86) | 2936 (+12) | 3580 (+12) | 4457 (-163) | 0 | 0 | 32.52 |
| 2 | I slide 500 credits across the table to Caron an… | 1590 (-284) | 3825 (+115) | 3197 (-50) | 3542 (-80) | 4433 (-238) | 0 | 0 | 24.62 |
| 3 | I find Halden by the town well and offer to carr… | 1588 (-346) | 4037 (+44) | 3249 (-70) | 3652 (+34) | 4462 (-163) | 0 | 0 | 32.00 |
| 4 | I leave Marrow's Crossing by the east gate and h… | 1531 (-358) | 4365 (+67) | 3197 (+15) | 3597 (+50) | 4261 (-157) | 0 | 0 | 44.23 |
| 5 | I walk up to the two toughs at the inn door and … | 1503 (-274) | 4348 (+85) | 3222 (+65) | 3771 (+102) | 4453 (-68) | 0 | 0 | 81.31 |
| 6 | I drop 200 credits on the ground between the tou… | 1623 (-344) | 4716 (+279) | 3479 (+151) | 3692 (+97) | 4669 (-12) | 0 | 0 | 106.17 |
| 7 | I sit across from Halden at his table, slide the… | 1619 (-273) | 4716 (+258) | 3418 (+140) | 3707 (+97) | 4454 (-123) | 0 | 0 | 86.11 |
| 8 | I pull out the brass key Halden gave me and try … | 1557 (-364) | 4803 (+336) | 3327 (+53) | 3579 (+30) | 4505 (-37) | 0 | 0 | 93.22 |
| 9 | I press my ear against the inn's stone wall and … | 1616 (-182) | 4686 (+347) | 3309 (+259) | 3550 (+26) | 4467 (+175) | 0 | 0 | 97.00 |
| 10 | I approach Matthew Estrada at the bar, grab his … | 1562 (-266) | 4615 (+196) | 3294 (-26) | 3592 (-53) | 4489 (-324) | 0 | 0 | 86.78 |
| 11 | Matthew's bodyguard draws a knife! I tackle him … | 1614 (-363) | 4622 (+126) | 3336 (-32) | 3531 (-4) | 4553 (-189) | 0 | 0 | 74.84 |
| 12 | I grab the ledger from my coat and sprint out th… | 1615 | 4600 | 3415 | 3708 | 4737 | 0 | 0 | 115.92 |
| 13 | I find a quiet corner at the dock and wrap my wo… | 1533 (-352) | 4788 (+230) | 3412 (+95) | 3731 (+108) | 4406 (-442) | 0 | 0 | 88.95 |
|  | TOTALS | 20534 | 57648 | 42791 | 47232 | 58346 | 0 | 0 | 963.66 |

**Total turns:** 13 · **Total duration:** 963.66s · **Avg/turn:** 74.13s
**Total tokens in:** 226,551 · **Total tokens out:** 12,782 · **Total LLM time:** 906.1s
**Total retries:** 0 · **Total parse failures:** 0

