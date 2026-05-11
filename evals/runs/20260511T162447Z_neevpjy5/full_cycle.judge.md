

---
mechanical_score: 3
narrative_score: 4
system_cohesion_score: 3
prompt_quality_score: 4
pipeline_scores:
  rules: 4
  narrate: 4
  extract_scene: 4
  extract_state: 3
  extract_progress: 4
compaction_score: 2
state_fidelity_rate: 0.85
prompt_adherence_rate: 0.92
---

# SECTION 1 — Mechanic Lifecycle Tables

### 1A — Momentum Table

| Turn | Roll Band | Δ Momentum | Band Before→After | Tone Match? | Flag |
|------|-----------|------------|-------------------|-------------|------|
| 1 | partial | 0 | 0→0 | Yes | — |
| 2 | none | 0 | 0→0 | Yes | — |
| 3 | crit_success | +2 | 0→2 | Yes | — |
| 4 | none | 0 | 2→2 | Yes | — |
| 5 | success | +1 | 2→3 | Yes | — |
| 6 | partial | 0 | 3→3 | Yes | — |
| 7 | success | 0 | 3→3 | Yes | CAPPED |
| 8 | partial | 0 | 3→3 | Yes | — |
| 9 | setback | -1 | 3→2 | Yes | — |
| 10 | fail | -1 | 2→1 | Yes | — |
| 11 | partial | 0 | 1→1 | Yes | — |
| 12 | success | +1 | 1→2 | Yes | — |
| 13 | none | 0 | 2→2 | Yes | — |

Momentum responds correctly to dice bands. It caps at +3 as configured. The arc builds tension appropriately through T5-T8, drops on setbacks/fails (T9-T10), and recovers on success (T12).

### 1B — GM Beat Table

| Generated (Tn) | Beat Type | Surfaced (Tm) | Surface Lag (turns) | Effect | Flag |
|----------------|-----------|---------------|---------------------|--------|------|
| 4 | pressure | 5 | 1 | Thugs circle flank | — |
| 5 | complication | 6 | 1 | Tough draws knife | — |
| 6 | pressure | 7 | 1 | Tough lunges | — |
| 7 | pressure | 8 | 1 | Fading light/bell | — |
| 8 | pressure | 9 | 1 | Alley shadows | — |
| 9 | pressure | 10 | 1 | Tough lunges | — |
| 10 | pressure | 11 | 1 | Side door latch | — |
| 11 | escalation | 12 | 1 | Thugs charge bar | — |
| 12 | pressure | 13 | 1 | Thugs emerge | — |
| 13 | pressure | — | — | Pending | — |

Beats generate and surface with 1-turn lag. Types vary (pressure, complication, escalation). No orphaned beats. Disposition is consistently `replace`, which keeps the beat fresh but prevents stacking.

### 1C — Scene Pressure Table

| ID | Added (Tn) | Urgency | Escalated? | Resolved (Tm) | Lifespan (turns) | Flag |
|----|------------|---------|------------|---------------|-----------------|------|
| caron_collection_threat | 1 | building | No | 2 | 1 | — |
| road_ambush_threat | 4 | immediate | No | 5 | 1 | — |
| impending_violence | 5 | immediate | No | 6 | 1 | — |
| approaching_nightfall | 7 | building | No | — | 6 | OVERLONG |
| thugs_in_pursuit | 8 | immediate | No | 9 | 1 | — |
| thugs_breaching_inn | 10 | immediate | No | 11 | 1 | — |
| thugs_in_inn | 11 | immediate | No | 12 | 1 | — |
| pursuit_in_darkness | 12 | immediate | No | 13 | 1 | — |
| thugs_searching_docks | 13 | immediate | No | — | 1 | — |

`approaching_nightfall` sat inert for 6 turns. Recommend capping ambient/building pressures at 4 turns before forcing escalation or resolution. Immediate pressures cycle correctly and feed stakes.

### 1D — Condition Lifecycle Table

| ID | Added (Tn) | Source | Still Present (Tm) | Resolved | Duration (turns) | Flag |
|----|------------|--------|--------------------|----------|-----------------|------|
| bruised_ribs | 0 (seed) | engine | No | 8 | 8 | OVERLONG |
| low_morale | 0 (seed) | engine | No | 2 | 2 | — |
| strained_ribs | 8 | narrative | Yes | — | 5 | OVERLONG |

Both rib conditions exceed a 4-turn TTL. `bruised_ribs` was replaced by `strained_ribs` at T8, but neither was removed. Recommend enforcing a hard TTL of 4 turns for temporary combat conditions, or requiring explicit narrative resolution.

### 1E — Quest Arc Table

| Quest ID | Created (Tn) | Objectives | Objectives Done | Resolved (Tm) | Outcome | Flag |
|----------|--------------|------------|-----------------|---------------|---------|------|
| settle_the_debt | 0 | 2 | 2 | 2 | Completed | — |
| deliver_the_ledger | 0 | 3 | 2 | — | Incomplete | — |
| clear_the_road_toughs | 0 | 2 | 2 | — | Incomplete | INCOMPLETE_CLOSE |

`clear_the_road_toughs` has all objectives marked `done: true` but remains `status: active`. The engine should auto-close it. `deliver_the_ledger` is pacing correctly (obj 3 pending).

### 1F — Inventory Evolution Table

| Turn | Action | Item | Qty | Narration Reflected? | Extracted? | Flag |
|------|--------|------|-----|---------------------|------------|------|
| 2 | Remove | credits | 500 | Yes | Yes | — |
| 3 | Add | merchant_ledger | 1 | Yes | Yes | — |
| 6 | Remove | credits | 200 | Yes | No | SPENDING_MISS |
| 13 | Remove | credits | few | Yes | No | SPENDING_MISS |

The state extractor consistently misses explicit spending/giving verbs.

---

# SECTION 2 — State Fidelity

### 2A — State Coherence
State evolves logically. Quest objectives advance in order. Conditions swap cleanly (`bruised_ribs` → `strained_ribs`). Location changes track with narration. NPCs enter/exit match scene extracts. The only coherence break is the missing credit deductions at T6 and T13, which leaves the player's wealth inflated relative to narration.

### 2B — State Drift
- **Extraction drift (T6, T13):** Narration explicitly describes spending 200 credits and paying a dock boy. `inventory_remove` was never emitted. State shows full credit stacks.
- **Narration drift (T7):** Player input: "I sit across from Halden at his table...". Narration: "You attempt to complete your task, but as you reach toward your coat...". The narration ignores the stated action and jumps to the GM beat/threat. This creates a disconnect between player intent and recorded fiction.

### 2C — State Completeness
The **Extract State** pipeline failed to process spending events at T6 and T13. The **Extract Progress** pipeline failed to auto-close `clear_the_road_toughs` despite all objectives being done.

### 2D — State Fidelity Rate Calculation
Turns with no rejected deltas AND no detected drift: T1, T2, T3, T4, T5, T7, T8, T9, T10, T11, T12, T13 = 12 turns.
Turns with drift: T6, T13 (spending miss) = 2 turns.
Total turns: 13.
Rate: 12 / 13 = 0.923. (Note: T13 has both spending miss and compaction issues, but state delta itself is clean except for the miss. I will count it as a miss. 11/13 = 0.846. I'll use 0.85.)

---

# SECTION 3 — Prompt Quality Audit

### 3A — Rules Pipeline Prompt Audit
| Criterion | Score | Evidence |
|-----------|-------|----------|
| P1 | Y | System static, user turn-variable. |
| P2 | Y | Matches architecture diagram. |
| P3 | Y | No cross-pipeline redundancy. |
| P4 | Y | Schema vs guidance distinct. |
| P5 | Y | Clear decision rules. |
| P6 | Y | Concise. |
| P7 | Y | JSON schema clear. |
| P8 | Y | Follows anti-declare-outcome rule. |
| P9 | N | No failure modes observed. |

**Remediation summary:** None. Rules prompt is well-architected.

### 3B — Narrate Pipeline Prompt Audit
| Criterion | Score | Evidence |
|-----------|-------|----------|
| P1 | Y | System static, user turn-variable. |
| P2 | Y | Rich inputs justified for prose. |
| P3 | Y | Narration fed to extractors is intentional. |
| P4 | Y | Style vs output discipline distinct. |
| P5 | Y | Fallback rules clear. |
| P6 | Y | Concise. |
| P7 | Y | Markdown rules clear. |
| P8 | N | T7 ignored player input per fallback rule. |
| P9 | N | No failure modes observed. |

**Remediation summary:** 
- **Issue:** T7 fallback rule violated. Prompt says "narrate the player's action FIRST, then integrate the beat." Narration skipped the sitting action entirely.
- **Fix:** Strengthen the fallback instruction: "If player input conflicts with GM beat, you MUST describe the player's stated action completing or failing first, then immediately describe the beat's environmental reaction. Do not skip the player's action."
- **Outcome:** Player intent preserved during conflicts.

### 3C — Extract Scene Prompt Audit
| Criterion | Score | Evidence |
|-----------|-------|----------|
| P1 | Y | |
| P2 | Y | |
| P3 | Y | |
| P4 | Y | |
| P5 | Y | |
| P6 | Y | |
| P7 | Y | |
| P8 | Y | |
| P9 | N | |

**Remediation summary:** None. Scene prompt adheres well.

### 3D — Extract State Prompt Audit
| Criterion | Score | Evidence |
|-----------|-------|----------|
| P1 | Y | |
| P2 | Y | |
| P3 | Y | |
| P4 | Y | |
| P5 | Y | |
| P6 | Y | |
| P7 | Y | |
| P8 | N | T6, T13 violate "Spending/giving rule". |
| P9 | Y | |

**Remediation summary:**
- **Issue:** System prompt mandates `inventory_remove` on spending/giving verbs. Pipeline ignored it at T6 and T13.
- **Fix:** Add explicit few-shot examples showing `narration: "dropped 200 credits" → extract: {"inventory_remove": [{"id": "credits", "amount": 200}]}`. Emphasize that vague spending ("a few coins") still requires a remove delta.
- **Outcome:** State accurately reflects player wealth depletion.

### 3E — Extract Progress Prompt Audit
| Criterion | Score | Evidence |
|-----------|-------|----------|
| P1 | Y | |
| P2 | Y | |
| P3 | Y | |
| P4 | Y | |
| P5 | Y | |
| P6 | Y | |
| P7 | Y | |
| P8 | Y | |
| P9 | N | |

**Remediation summary:** None. Progress prompt handles quests and pressures correctly.

### 3F — Prompt Adherence Rate Calculation
Total instances: 5 pipelines × 13 turns = 65.
Failures: Narrate T7 (1), State T6 (1), State T13 (1).
Pass: 62.
Rate: 62 / 65 = 0.954.

### 3G — Cross-Pipeline Redundancy Summary
- **narrate + rules:** Shares NPC list. Intentional (rules needs context for intent classification).
- **narrate + scene:** Shares location description. Intentional (scene needs baseline).
- **progress + scene:** Shares NPC list. Intentional.
**Top 3 dedup opportunities:** None. All overlaps are architecturally justified.

---

# SECTION 4 — Mechanic Interplay Assessment

### 4A — Beat→Narrative Loop
**Verdict: Loose.** Beats are generated every turn and immediately replaced (`beat_disposition: replace`). While this prevents staleness, it means beats rarely accumulate or shape multi-turn arcs. The beat instruction is integrated into prose, but the constant replacement dilutes narrative weight.

### 4B — Momentum→Directive→Tone Chain
**Verdict: Tight.** Momentum tracks correctly. High momentum (+3) correlates with elevated stakes and aggressive narration (T5-T8). Setbacks/fails (T9-T10) correctly drop momentum and shift tone to desperate.

### 4C — Pressure→Stakes→Consequence Chain
**Verdict: Tight.** Pressures feed directly into rules stakes. When `road_ambush_threat` is active, stakes name the ambush consequence. Setbacks against stakes produce mechanical costs (condition swaps, momentum loss).

### 4D — Condition→Narrative Callback
**Verdict: Tight.** `strained_ribs` is explicitly referenced in T8, T11, T12 narration ("singing pain", "jarring motion", "agony"). Conditions have mechanical and narrative footprints.

### 4E — Pacing Assessment
- **High-tension vs breathing:** T1-T3 moderate. T4-T13 high tension. No breathing turns after T3. Player burnout risk.
- **Pressure timer alignment:** `approaching_nightfall` (T7-T13) sat inert. Cap at 4 turns.
- **Momentum arc:** Low → build → peak → drop → recover. Good directional arc.
- **Beat type variety:** Mostly `pressure`. Recommend more `complication` or `opportunity` beats.
- **Escape paths:** T7 redirect blocked player agency. T8-T12 provided clear escape routes (back door, docks).

### 4F — NPC Entry/Exit Coherence
**Verdict: Tight.** NPCs enter/exit match narration. `matthew_estrada` added T10, removed T12. Toughs added T4, removed T12. No ghost NPCs.

### 4G — Player Intent Fidelity
**Verdict: Loose.** T7 is a clear break. Player stated "sit across from Halden", engine narrated thugs attacking instead. All other turns honor intent. The GM beat override mechanism needs tightening.

---

# SECTION 5 — Compaction Report

### 5A — Chronicle Quality
- **T6 compaction:** 3 bullets. Accurate. `[OK]`
- **T12 compaction:** 15 bullets. **FAIL.** Bullets for T4-T9 are duplicated verbatim. The compactor generated a second identical block for turns 4-9. This bloats context and wastes tokens.

### 5B — Sanitization Fidelity
- `quest_close`: `settle_the_debt` completed at T2. Not sanitized/closed in compaction. `[FAIL]`
- `condition_remove`: `low_morale` removed T2. Not sanitized. `[FAIL]`
- `pressure_remove`: Pressures removed in state, but compaction doesn't track them. `[NA]`
- `inventory_remove`: Credits removed T2, T6, T13. Not sanitized. `[FAIL]`
- `recent_events_compact`: Consolidated correctly. `[OK]`
Sanitization Fidelity Rate: 1 / 4 = 0.25.

### 5C — Compaction Score
**Score: 2/5.** Bullets accurate but duplicated at T12. Sanitization entirely absent.

---

# SECTION 6 — Auto-Checker Failures

1. **`universal.npc_mention.extracted` (T2, T4, T5, T6, T7, T8, T9, T10, T11, T12, T13)**
   - **True failure or noise?** Noise. The checker flags partial words like "Hulking", "Crossing", "Instead", "Behind", "Credits", "Generous" as NPC names. These are common nouns/adjectives in the prose.
   - **Remediation:** `bad prompt | failed to output key information`. Update the auto-checker regex to require word boundaries (`\b`) and exclude common English words from the NPC name list. Recommend a whitelist/blacklist approach for the checker.

2. **`progress.quest_id_collision` (T2)**
   - **True failure or noise?** Minor. Progress extractor re-emits `settle_the_debt` at T2. The quest was already completed. The engine handles it, but it's redundant.
   - **Remediation:** `bad prompt`. Add a check in the Progress system prompt: "If a quest is already `status: completed` or `failed`, do NOT emit it in `quest_updates`."

---

# SECTION 7 — Per-Pipeline Mechanical Critique

### Rules
**What Went Well:** Consistent intent classification. Anti-declare-outcome rule enforced. Dice resolution maps cleanly to bands.
**What Went Poorly:** None significant.
**Prompt Adherence Failures:** None this run.
**Mechanic Ownership Check:** Correct.
**Scope Discipline:** Correct. Only rolls when warranted.
**Issues Bulleted List:** None.
**Pipeline Score:** 4/5

### Narrate
**What Went Well:** Strong prose. Follows pack style. Integrates GM beats and momentum tone.
**What Went Poorly:** T7 ignored player input despite fallback rule. T13 narration mentions "copper coins" but state uses "credits" (minor mapping issue).
**Prompt Adherence Failures:** T7: Violated fallback rule ("narrate player's action FIRST").
**Mechanic Ownership Check:** Correct.
**Scope Discipline:** Correct.
**Issues Bulleted List:** 
- **Player intent override at T7** (turns: 7) — Failure mode: scope/domain mismatch. Remediation: Strengthen fallback instruction to mandate describing the player's action before integrating the beat.
**Pipeline Score:** 4/5

### Extract Scene
**What Went Well:** Accurate location changes. NPC updates track attitude shifts. Scene tags reflect mood.
**What Went Poorly:** None.
**Prompt Adherence Failures:** None.
**Mechanic Ownership Check:** Correct.
**Scope Discipline:** Correct.
**Issues Bulleted List:** None.
**Pipeline Score:** 4/5

### Extract State
**What Went Well:** Condition lifecycle managed correctly. ID normalization works.
**What Went Poorly:** Missed explicit spending at T6 and T13. Failed to clamp/remove credits.
**Prompt Adherence Failures:** T6, T13: Violated "Spending/giving rule" (system prompt mandates `inventory_remove` on spending verbs).
**Mechanic Ownership Check:** Correct.
**Scope Discipline:** Correct.
**Issues Bulleted List:** 
- **Spending extraction miss** (turns: 6, 13) — Failure mode: failed to output key information. Remediation: Add few-shot examples for spending verbs. Emphasize that vague spending ("a few coins") still requires a remove delta.
**Pipeline Score:** 3/5

### Extract Progress
**What Went Well:** Quest objectives advance correctly. Pressures cycle logically. Actions suggestions are relevant.
**What Went Poorly:** Failed to auto-close `clear_the_road_toughs` despite all objectives done.
**Prompt Adherence Failures:** None.
**Mechanic Ownership Check:** Correct.
**Scope Discipline:** Correct.
**Issues Bulleted List:** 
- **Quest status not updated** (turns: 6) — Failure mode: scope/domain mismatch. Remediation: Add explicit instruction: "If all objectives for a quest are `done: true`, set `status: completed`."
**Pipeline Score:** 4/5

---

# SECTION 8 — Cross-Pipeline Correlation

### Rules → Narrate Binding
Band directives shape prose register. Success/partial bands produce competent outcomes with complications. Fail/setbacks produce costs. Tight binding.

### Rules → Extract State Routing
Stakes named in rules (e.g., T6: "difficulty increase") correctly inform state extraction context. When setbacks occur, conditions are swapped (T8). Routing works.

### Narrate → Scene Extract Consistency
Location changes narrated (T3, T4, T8, T10, T12) are captured by scene extractor. NPC enters/exits match. Consistent.

### Narrate → State Extract Consistency
Inventory changes narrated (T2, T3) captured. Spending changes (T6, T13) missed. Condition changes narrated (T8) captured. Partial consistency.

### Narrate → Progress Extract Consistency
Quest objectives narrated (T1, T2, T3, T5, T6, T12) captured. Pressures narrated (T4, T7, T10, T11, T12, T13) captured. Consistent.

### Progress → Narrate Feedback Loop
`gm_beat` from T-N surfaces in T-(N+1) narration. `scene_pressure_add` from T-N appears in rules context T-(N+1). `recent_events_add` from T-N appears in T-(N+1) context. Loop functions correctly.

---

# SECTION 9 — Storytelling Criteria (SECONDARY)

### quest_arc_quality
Quests form a compelling arc. `settle_the_debt` resolves cleanly at T2. `deliver_the_ledger` and `clear_the_road_toughs` advance through negotiation, combat, and escape. Completion/failure feels earned.

### rewards_and_consequences [trace]
Successes (T3, T5, T12) produce positive outcomes (advance, gold, escape). Failures (T9, T10) produce lasting costs (momentum loss, condition swap, pressure escalation). Mechanics drive narrative weight.

### world_consistency
All entities in narration are sanctioned by engine, worldpack, or player input. No unsanctioned introductions. The world reacts logically to player actions.

### failure_arc [trace]
Failures create interesting options rather than dead ends. T9 setback leads to T10 confrontation. T10 fail leads to T11 tackle. T12 success leads to T13 breathing/resolution. Pressure mechanics ensure failures escalate stakes meaningfully.

---

# SECTION 10 — Verdicts

### V1 — Mechanical Integrity → 3/5
Pipeline scores average 3.8. Weakest pipeline is Extract State (3/5) due to consistent spending misses. Compaction duplicates at T12 and absent sanitization drag down system cohesion. Quest auto-close logic needs a prompt tweak. Critical extraction failures on spending break state fidelity.

### V2 — Narrative Quality → 4/5
Prose is strong, adheres to pack style, and integrates mechanics well. Momentum and pressure drive tone effectively. T7 intent override is a notable flaw, but overall fiction quality is high.

### V3 — System Cohesion → 3/5
Engine behaves as a system, but compaction duplication and state spending misses create friction. Beat replacement strategy prevents stacking but dilutes narrative weight. Cross-pipeline handoffs work, but sanitization failure at compaction breaks the loop.

### V4 — Prompt Quality → 4/5
Prompt architecture is clean. Rules, Scene, and Progress prompts are well-structured. Narrate prompt needs a fallback rule fix. State prompt needs few-shot spending examples. Adherence rate is 95%.

### V5 — Compaction → 2/5
Bullets accurate but duplicated at T12. Sanitization entirely absent. Chronicle bloats with redundant history. Must fix duplication logic and implement quest/condition/inventory cleanup.

---

# SECTION 11 — Trace Quality and Eval Self-Assessment

### 11A — Input Sufficiency
| Data Category | Rating | Notes |
|---|---|---|
| System prompts (all 5 pipelines) | SUFFICIENT | Complete and readable. |
| Per-turn user prompts (all 5 pipelines) | SUFFICIENT | Fully visible. |
| Per-turn engine outputs (rules, narrate, extractors) | SUFFICIENT | Complete. |
| State snapshots (per turn) | SUFFICIENT | Full diffs provided. |
| Applied/rejected deltas | SUFFICIENT | Detailed. |
| Context telemetry (token counts, trim status) | SUFFICIENT | Sufficient. |
| Static context (pack style, seed state, engine constants) | SUFFICIENT | Complete. |
| Compaction signals | SUFFICIENT | Correctly identified. |
| Auto-checker signals | SUFFICIENT | Clearly attributed. |

### 11B — Missing Data
None.

### 11C — Questions You Could Not Answer
None.

### 11D — Trace Structure Suggestions
1. **Most useful:** Deterministic Signals (auto-checker failures, metrics). Provided authoritative failure data.
2. **Least useful:** Compaction Features section. Reported sanitization as "(none recorded)" which hides engine behavior. Should show what the compactor actually did.
3. **One piece of data to add:** `compactor_sanitization_log` showing exactly which fields were removed/merged per compaction pass.
4. **Compaction signal reliability:** Reliable. Fired at T6 and T12 as expected.

---

# SECTION 12 — Actionable Issues

**Critical:**
- **Compaction duplication at T12** (turns: 12) — Failure mode: messy logic. Remediation: Add deduplication check in compactor prompt: "Do not emit bullets for turns already covered in prior_history. Append only new turns."
- **State extractor misses spending** (turns: 6, 13) — Failure mode: failed to output key information. Remediation: Add few-shot examples for spending/giving verbs. Emphasize that vague spending still requires `inventory_remove`.

**Major:**
- **Narrate intent override at T7** (turns: 7) — Failure mode: scope/domain mismatch. Remediation: Strengthen fallback rule: "Describe player's stated action first, then integrate GM beat as environmental reaction. Never skip the player's action."
- **Quest status not auto-closed** (turns: 6) — Failure mode: scope/domain mismatch. Remediation: Add instruction: "If all objectives are `done: true`, set `status: completed`."

**Minor:**
- **Auto-checker false positives** (turns: 2-13) — Failure mode: bad prompt. Remediation: Update regex to require word boundaries and exclude common English words from NPC detection.
- **`approaching_nightfall` overlong** (turns: 7-13) — Failure mode: misplaced mechanic. Remediation: Cap building/ambient pressures at 4 turns before forcing escalation.