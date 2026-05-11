# Eval Report — `full_cycle`

**Pack:** `eval-pack` · **Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8` · **Temp override:** `None`  
**Started:** 2026-05-11T16:24:47.590014+00:00 · **Finished:** 2026-05-11T16:32:15.858272+00:00  
**Output dir:** `/Users/pwilson/Repos/ccya/evals/runs/20260511T162447Z_neevpjy5`  
**Compared against:** _(no prior run found)_

## Judge Summary

**Mechanical:** 3/5  
**Narrative:** 4/5  
**System Cohesion:** 3/5  
**Prompt Quality:** 4/5  
**Compaction:** 2/5  
**State Fidelity:** 85.0%  
**Prompt Adherence:** 92.0%
**Rubric:** `/Users/pwilson/Repos/ccya/evals/rubrics/default.md`
**Judge model:** `mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit`

**Pipeline scores:**
- rules: 4/5
- narrate: 4/5
- extract_scene: 4/5
- extract_state: 3/5
- extract_progress: 4/5

**Trace:** [`full_cycle.trace.md`](full_cycle.trace.md)
**Judge response:** [`full_cycle.judge.md`](full_cycle.judge.md)

## ✅ No flags

No regressions, retries, failures, or judge score drops detected.


## Judge Verdict (full)

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

## Auto-Checker

**133 passed, 21 failed**

| Turn | Assertion | Result | Detail |
|---|---|---|---|
| 1 | `rules.rolled` | ❌ | rolled=True |
| 1 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 1 | `universal.pending_gm_beat.consumed` | ✅ | (first turn) |
| 1 | `universal.location_change.applied` | ✅ | (no change) |
| 1 | `universal.narrate.binding_present` | ✅ | binding directive included |
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
| 2 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Credits', 'Generous'] |
| 2 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 2 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 2 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 2 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 2 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 2 | `progress.quest_id_collision` | ❌ | quest_updates re-creates already-completed quest id='settle_the_debt' |
| 3 | `rules.rolled` | ✅ | rolled=True |
| 3 | `extract.progress.quest_updates` | ✅ | quest_updates[deliver_the_ledger] found |
| 3 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 3 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 3 | `universal.location_change.applied` | ✅ | marrows_crossing -> marrows_crossing_square |
| 3 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 3 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 3 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 3 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 3 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 3 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 3 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 4 | `rules.rolled` | ✅ | rolled=False |
| 4 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=4 |
| 4 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 4 | `universal.location_change.applied` | ✅ | marrows_crossing_square -> east_gate_road |
| 4 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 4 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Marrow', 'Crossing'] |
| 4 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 4 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 4 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 4 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 4 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 5 | `rules.rolled` | ✅ | rolled=True |
| 5 | `extract.scene.scene_tags` | ❌ | scene_tags[combat] not found |
| 5 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=5 |
| 5 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 5 | `universal.location_change.applied` | ✅ | (no change) |
| 5 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 5 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Hulking'] |
| 5 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
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
| 6 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 6 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Hulking', 'Instead'] |
| 6 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 6 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 6 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 6 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 6 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 7 | `extract.progress.quest_updates` | ❌ | quest_updates[deliver_the_ledger] not found |
| 7 | `extract.progress.quest_status` | ❌ | quest[deliver_the_ledger] not found in quest_updates |
| 7 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=7 |
| 7 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 7 | `universal.location_change.applied` | ✅ | (no change) |
| 7 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 7 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Hulking', 'Marrow', 'Crossing'] |
| 7 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 7 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 7 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 7 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 7 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 8 | `rules.rolled` | ✅ | rolled=True |
| 8 | `extract.state.inventory_remove` | ❌ | inventory_remove[brass_key] not found |
| 8 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 8 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 8 | `universal.location_change.applied` | ✅ | east_gate_road -> crossed_keys_inn_entrance |
| 8 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 8 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Instead'] |
| 8 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 8 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 8 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 8 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 8 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 9 | `rules.rolled` | ✅ | rolled=True |
| 9 | `extract.scene.scene_tags` | ❌ | scene_tags[social] not found |
| 9 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=9 |
| 9 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 9 | `universal.location_change.applied` | ✅ | (no change) |
| 9 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 9 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Hulking'] |
| 9 | `universal.recent_events.ring_bounded` | ✅ | 6 entries |
| 9 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 9 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 9 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 9 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 10 | `rules.rolled` | ✅ | rolled=True |
| 10 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 10 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 10 | `universal.location_change.applied` | ✅ | crossed_keys_inn_entrance -> crossed_keys_inn_interior |
| 10 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 10 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Behind', 'Matthew', 'Estrada'] |
| 10 | `universal.recent_events.ring_bounded` | ✅ | 6 entries |
| 10 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 10 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 10 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 10 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 11 | `rules.rolled` | ✅ | rolled=True |
| 11 | `extract.scene.scene_tags` | ✅ | scene_tags[combat] found |
| 11 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=11 |
| 11 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 11 | `universal.location_change.applied` | ✅ | (no change) |
| 11 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 11 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Hulking', 'Matthew', 'Estrada'] |
| 11 | `universal.recent_events.ring_bounded` | ✅ | 7 entries |
| 11 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 11 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 11 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 11 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 12 | `rules.rolled` | ❌ | rolled=True |
| 12 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=12 |
| 12 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 12 | `universal.location_change.applied` | ✅ | crossed_keys_inn_interior -> river_docks |
| 12 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 12 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Matthew', 'Estrada'] |
| 12 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 12 | `universal.scene.npc_cap` | ✅ | 0 NPCs |
| 12 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 12 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 12 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 13 | `rules.rolled` | ✅ | rolled=False |
| 13 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=13 |
| 13 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 13 | `universal.location_change.applied` | ✅ | (no change) |
| 13 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 13 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed', 'Hulking'] |
| 13 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 13 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 13 | `universal.pc.condition_no_dupes` | ✅ | 1 conditions, no dupes |
| 13 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 13 | `universal.momentum.band_delta` | ✅ | (no roll) |

## Turn Metrics

| # | input | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | retries | parse_fail | duration_s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | Walk over to Caron's table and sit down across f… | 1403 | 2999 | 2439 | 2937 | 4211 | 0 | 0 | 34.00 |
| 2 | I slide 500 credits across the table to Caron an… | 1729 | 3180 | 2687 | 2911 | 4448 | 0 | 0 | 25.75 |
| 3 | I find Halden by the town well and offer to carr… | 1710 | 3482 | 2735 | 2939 | 4483 | 0 | 0 | 31.08 |
| 4 | I leave Marrow's Crossing by the east gate and h… | 1727 | 3671 | 2774 | 3057 | 4428 | 0 | 0 | 35.48 |
| 5 | I walk up to the two toughs at the inn door and … | 1857 | 4089 | 2882 | 2980 | 4694 | 0 | 0 | 32.53 |
| 6 | I drop 200 credits on the ground between the tou… | 1794 | 4176 | 2820 | 2994 | 4621 | 0 | 0 | 39.31 |
| 7 | I sit across from Halden at his table, slide the… | 1781 | 4320 | 2763 | 2941 | 4569 | 0 | 0 | 30.47 |
| 8 | I pull out the brass key Halden gave me and try … | 1742 | 4206 | 2737 | 2940 | 4521 | 0 | 0 | 30.41 |
| 9 | I press my ear against the inn's stone wall and … | 1722 | 4126 | 2725 | 2953 | 4529 | 0 | 0 | 29.17 |
| 10 | I approach Matthew Estrada at the bar, grab his … | 1754 | 4060 | 2840 | 3036 | 4689 | 0 | 0 | 36.09 |
| 11 | Matthew's bodyguard draws a knife! I tackle him … | 1803 | 4148 | 2795 | 2962 | 4634 | 0 | 0 | 34.85 |
| 12 | I grab the ledger from my coat and sprint out th… | 1784 | 4299 | 2844 | 2940 | 4729 | 0 | 0 | 57.91 |
| 13 | I find a quiet corner at the dock and wrap my wo… | 1672 | 4394 | 2604 | 2977 | 4416 | 0 | 0 | 31.15 |
|  | TOTALS | 22478 | 51150 | 35645 | 38567 | 58972 | 0 | 0 | 448.19 |

**Total turns:** 13 · **Total duration:** 448.19s · **Avg/turn:** 34.48s
**Total tokens in:** 206,812 · **Total tokens out:** 170,577 · **Total LLM time:** 414.4s
**Total retries:** 0 · **Total parse failures:** 0

