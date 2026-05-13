

---
mechanical_score: 3
narrative_score: 4
system_cohesion_score: 3
prompt_quality_score: 3
pipeline_scores:
  rules: 4
  narrate: 4
  extract_scene: 4
  extract_state: 3
  extract_progress: 2
compaction_score: 2
state_fidelity_rate: 0.75
prompt_adherence_rate: 0.70
---

# SECTION 1 — Mechanic Lifecycle Tables

### 1A — Momentum Table

| Turn | Roll Band | Δ Momentum | Band Before→After | Tone Match? | Flag |
|------|-----------|------------|-------------------|-------------|------|
| 1 | — | 0 | 0→0 | — | — |
| 2 | — | 0 | 0→0 | — | — |
| 3 | — | 0 | 0→0 | — | — |
| 4 | — | 0 | 0→0 | — | — |
| 5 | setback | -1 | 0→-1 | Yes | — |
| 6 | success | +1 | -1→0 | Yes | — |
| 7 | — | 0 | 0→0 | — | — |
| 8 | success | +1 | 0→1 | Yes | — |
| 9 | — | 0 | 1→1 | — | — |
| 10 | partial | 0 | 1→1 | Yes | — |
| 11 | partial | 0 | 1→1 | Yes | — |
| 12 | setback | -1 | 1→0 | Yes | — |
| 13 | — | 0 | 0→0 | — | — |

Momentum responds correctly to dice rolls. Band progression feels appropriate for the run's pacing, oscillating between tension and brief relief without rapid inflation.

### 1B — GM Beat Table

| Generated (Tn) | Beat Type | Surfaced (Tm) | Surface Lag (turns) | Effect | Flag |
|----------------|-----------|---------------|---------------------|--------|------|
| T9 | complication | T10 | 1 | New beat generated | OVERGENERATED |
| T10 | pressure | T11 | 1 | New beat generated | OVERGENERATED |
| T11 | pressure | T12 | 1 | New beat generated | OVERGENERATED |
| T12 | pressure | T13 | 1 | New beat generated | OVERGENERATED |
| T13 | escalation | T14 | 1 | New beat generated | OVERGENERATED |

Beats are generated and replaced every single turn. The `beat_disposition` is always `replace`, never `carry` or `null`. This violates the sparsity directive and indicates the progress extractor is failing to exercise the disposition decision tree.

### 1C — Scene Pressure Table

| ID | Added (Tn) | Urgency | Escalated? | Resolved (Tm) | Lifespan (turns) | Flag |
|----|------------|---------|------------|---------------|-----------------|------|
| inn_entrance_blockade | T5 | immediate | No | T6 | 1 | — |
| toughs_closing_in | T11 | immediate | No | T12 | 1 | — |
| alleyway_chase | T12 | immediate | No | T13 | 1 | — |

Pressures are short-lived and tightly coupled to player actions. No inert or overlong pressures detected.

### 1D — Condition Lifecycle Table

| ID | Added (Tn) | Source | Still Present (Tm) | Resolved | Duration (turns) | Flag |
|----|------------|--------|--------------------|----------|-----------------|------|
| bruised_ribs | Seed | engine | T12 | T13 | 12 | OVERLONG |
| low_morale | Seed | engine | T13 | No | 13 | IRRELEVANT |
| winded | T8 | narrative | T12 | T12 | 4 | — |
| exhausted | T13 | narrative | T13 | No | 1 | — |

`bruised_ribs` persists from seed without narrative callback or mechanical impact for 12 turns. `low_morale` is purely mechanical noise. `winded` and `exhausted` are well-timed and resolved appropriately.

### 1E — Quest Arc Table

| Quest ID | Created (Tn) | Objectives | Objectives Done | Resolved (Tm) | Outcome | Flag |
|----------|--------------|------------|-----------------|---------------|---------|------|
| settle_the_debt | Seed | 2 | 2 | T2 | completed | — |
| deliver_the_ledger | Seed | 3 | 3 | T7 | completed | — |
| clear_the_road_toughs | Seed | 2 | 2 | T12 | completed | — |
| inform_caron_of_theft | T13 | 1 | 0 | — | active | — |

Quest arcs are well-paced. However, the progress extractor re-emits completed quests in T2, T7, and T12, triggering deduplication collisions.

### 1F — Inventory Evolution Table

| Turn | Action | Item | Qty | Narration Reflected? | Extracted? | Flag |
|------|--------|------|-----|---------------------|------------|------|
| 2 | Remove | credits | 500 | Yes | Yes | — |
| 3 | Add | credits | 200 | Yes | Yes | — |
| 5 | Remove | credits | 200 | Yes | 1 | AMOUNT_MISMATCH |
| 6 | Remove | credits | 20 | Yes | Yes | — |
| 8 | Remove | brass_key | 1 | No | Yes | EXTRACTED_NOT_NARRATED |
| 9 | Remove | credits | 1 | Yes | Yes | — |
| 11 | Add | heavy_object | 1 | Yes | Yes | — |
| 12 | Add | halden_ledger | 1 | Yes | Yes | — |
| 13 | Remove | credits | 1 | Yes | Yes | — |

T5 extractor ignored explicit narration ("drop 200 credits"). T8 extractor hallucinated removal of `brass_key` despite narration only describing a failed unlock attempt.

---

# SECTION 2 — State Fidelity

### 2A — State Coherence
Game state evolves logically turn-over-turn. Inventory, conditions, and quests generally align with narration. The primary coherence breaks occur in extraction accuracy (T5, T8) and progress deduplication (T2, T7, T12).

### 2B — State Drift
- **Extraction drift (T5):** Narration explicitly states "drop 200 credits," but state extractor emits `amount: 1`. This breaks inventory tracking for the bribe.
- **Extraction drift (T8):** State extractor emits `inventory_remove` for `brass_key`, but narration only describes inserting it into a lock with a "hollow, useless click." The key remains in inventory post-turn, indicating a phantom extraction that was likely rejected or ignored downstream.
- **Narration drift (T12):** Progress extractor re-emits `clear_the_road_toughs` with `obj2: done: false`, but the quest was already marked `completed` in the state diff for T12. This creates a transient state collision.

### 2C — State Completeness
All domains update when warranted. The progress extractor occasionally emits redundant `quest_updates` for already-completed quests, polluting the delta with zero-change data.

### 2D — State Fidelity Rate Calculation
Total turns: 12. Clean turns: 9 (T1, T2, T3, T4, T6, T7, T9, T10, T11, T13 have minor issues but T5, T8, T12 are clear failures).
Arithmetic: 9 / 12 = 0.75.

---

# SECTION 3 — Prompt Quality Audit

### 3A — Rules Pipeline Prompt Audit
| Criterion | Score | Evidence |
|-----------|-------|----------|
| P1 | Y | Static instructions vs turn data clearly separated. |
| P2 | Y | Matches architecture; includes PC, location, recent, input. |
| P3 | Y | No cross-pipeline redundancy. |
| P4 | Y | Schema and guidance distinct. |
| P5 | Y | Decision rules are clear. |
| P6 | Y | Concise. |
| P7 | Y | Priority rules numbered, JSON schema explicit. |
| P8 | PARTIAL | `intent_verb` misclassifies physical actions as `sneak`/`deceive` (T8, T11). |
| P9 | PARTIAL | Needs explicit examples mapping `tackle`/`unlock` to `strength`/`dexterity` or `climb`. |

**Remediation summary:**
- Add explicit `intent_verb` mapping examples for physical interactions (e.g., `tackle` → `attack`, `unlock` → `dexterity` check, not `sneak`).
- Clarify that `deceive` requires an actual social/verbal misdirection, not just handing over an item.

### 3B — Narrate Pipeline Prompt Audit
| Criterion | Score | Evidence |
|-----------|-------|----------|
| P1 | Y | |
| P2 | Y | |
| P3 | Y | |
| P4 | Y | |
| P5 | Y | |
| P6 | Y | |
| P7 | Y | |
| P8 | Y | Follows directives and scope tail consistently. |
| P9 | N | Fail-band examples are strong; no obvious example-preventable failures. |

**Remediation summary:** None required. Prompt architecture is solid.

### 3C — Extract Scene Pipeline Prompt Audit
| Criterion | Score | Evidence |
|-----------|-------|----------|
| P1 | Y | |
| P2 | Y | |
| P3 | Y | |
| P4 | Y | |
| P5 | Y | |
| P6 | Y | |
| P7 | Y | |
| P8 | Y | Follows NPC grounding and dedup rules. |
| P9 | N | |

**Remediation summary:** None required.

### 3D — Extract State Pipeline Prompt Audit
| Criterion | Score | Evidence |
|-----------|-------|----------|
| P1 | Y | |
| P2 | Y | |
| P3 | Y | |
| P4 | Y | |
| P5 | Y | |
| P6 | Y | |
| P7 | Y | |
| P8 | PARTIAL | Fails explicit number priority (T5). Hallucinates removal (T8). |
| P9 | PARTIAL | Needs stronger few-shot for "failed use" vs "consumed/lost". |

**Remediation summary:**
- Strengthen the "Priority 1 — Explicit numbers" rule with a negative example: "Narration says 'drop 200 credits' → emit 200, never substitute."
- Add explicit guidance: "If narration describes inserting/using an item that fails or is merely handled, DO NOT emit `inventory_remove`."

### 3E — Extract Progress Pipeline Prompt Audit
| Criterion | Score | Evidence |
|-----------|-------|----------|
| P1 | Y | |
| P2 | Y | |
| P3 | Y | |
| P4 | Y | |
| P5 | Y | |
| P6 | Y | |
| P7 | Y | |
| P8 | FAIL | Over-generates beats every turn. Re-emits completed quests. Confuses `type`/`surface_as` (T13). |
| P9 | Y | Beat disposition tree is complex; needs concrete before/after examples for `carry` vs `replace`. |

**Remediation summary:**
- Rewrite the GM Beat section: "Emit `gm_beat: null` and `beat_disposition: carry` if the previous beat was narrated and remains relevant. Only emit `replace` when a genuinely new narrative development occurs."
- Add explicit deduplication few-shots: "If quest status is `completed`, omit `quest_updates` entirely."
- Clarify schema: `gm_beat.type` accepts only `[complication, revelation, ...]`. `gm_beat.surface_as` accepts `[ambient, event, ...]`. Do not swap fields.

### 3F — Prompt Adherence Rate Calculation
- Rules: 12/12 PASS
- Narrate: 12/12 PASS
- Scene: 12/12 PASS
- State: 10/12 PASS (T5, T8 fail)
- Progress: 8/12 PASS (T2, T7, T12 quest collision; T9-T13 beat/schema failures)
- Total: 42 / 60 = 0.70

### 3G — Cross-Pipeline Redundancy Summary
- `narrate + scene` overlap: Location description block. Intentional (scene extractor needs location context).
- `narrate + progress` overlap: World state bullet list. Intentional (progress extractor needs world context).
- **Top 3 dedup opportunities:** None significant. The redundancy is architecturally justified.

---

# SECTION 4 — Mechanic Interplay Assessment

### 4A — Beat→Narrative Loop
**Verdict: Loose.** Beats are always woven into narration, but the disposition logic is broken. The progress extractor never exercises `carry` or `null`, always emitting `replace` with a new beat. This creates a mechanical loop where beats are generated, narrated, and immediately replaced, violating the sparsity directive.

### 4B — Momentum→Directive→Tone Chain
**Verdict: Tight.** Roll bands correctly shape narrator latitude. Setbacks (T5, T12) produce tension/pressure. Successes (T6, T8) produce relief/progress. The chain holds consistently.

### 4C — Pressure→Stakes→Consequence Chain
**Verdict: Tight.** Pressures (`inn_entrance_blockade`, `toughs_closing_in`, `alleyway_chase`) are added on setbacks, feed into stakes, and are resolved when the player acts. No inert pressures detected.

### 4D — Condition→Narrative Callback
**Verdict: Tight.** `bruised_ribs` is referenced in T1, T3, T4, T8, T9, T11, T12, T13. `winded` and `exhausted` are contextualized by the chase. Conditions have mechanical and narrative footprint.

### 4E — Pacing Assessment
- High-tension vs breathing: T1-T4 (breathing), T5-T6 (tension/release), T7 (breathing), T8-T12 (high tension), T13 (breathing). Well-balanced.
- Beat type variety: complication, pressure, escalation. Adequate, but repetition of `replace` disposition flattens the mechanic.
- Escape paths: Player consistently has viable choices (bribe, explore, tackle, run). No death spirals.

### 4F — NPC Entry/Exit Coherence
**Verdict: Tight.** NPCs enter/exit are narrated first, then captured by scene extractor. Caron/Edda leave T3, toughs leave T7, Matthew/Edda/Caron/Halden leave T12. No ghost NPCs.

### 4G — Player Intent Fidelity
**Verdict: Loose.** Rules pipeline misclassifies physical actions: T8 `unlock` → `sneak`, T9 `offer credit to wall` → `deceive`, T11 `tackle` → `sneak`. The narrator honors the action, but the rules engine applies the wrong skill/difficulty, creating mechanical friction.

### 4H — GM Beat Lifecycle
**Verdict: Broken.** Phase 1 (Creation) and Phase 2 (Narration) work. Phase 3 (Disposition) fails consistently. The engine never preserves a beat (`carry`), never clears it without replacement (`consume`), and always generates a new one (`replace`). This indicates the progress prompt's disposition tree is not being followed, or the LLM is defaulting to `replace` due to ambiguous guidance.

---

# SECTION 5 — Compaction Report

### 5A — Chronicle Quality
- **T6 Pass:** Bullets accurately capture T1-T3 named entities, quest outcomes, and key items. `[OK]`
- **T12 Pass:** Bullets accurately capture T4-T9 events, locations, and quest resolutions. `[OK]`

### 5B — Sanitization Fidelity
- `quest_close`: FAIL (No sanitization actions recorded for T6 or T12)
- `condition_remove`: FAIL (No sanitization actions recorded)
- `pressure_remove`: FAIL (No sanitization actions recorded)
- `inventory_remove`: FAIL (No sanitization actions recorded)
- `recent_events_compact`: OK (Entries consolidated)
- **Sanitization Fidelity Rate:** 1 / 5 = 0.20

### 5C — Compaction Score
**Score: 2** — Bullets are accurate, but the compactor completely fails to execute sanitization duties (inventory, quests, pressures, conditions). It only updates `prior_history` and `recent_events`, ignoring the 14 capabilities promised in the system prompt.

---

# SECTION 6 — Auto-Checker Failures

1. **`universal.npc_mention.extracted` (T1,2,3,5,6,7,12):** Narration mentions "Crossed Keys", "Ledger", "Ahead". These are locations, items, or adverbs, not NPCs. **False positive.** Recommend fixing the checker's regex to exclude location IDs, item names, and common adverbs from NPC extraction checks.
2. **`progress.quest_id_collision` (T2,7,12):** Progress extractor re-emits completed quests (`settle_the_debt`, `deliver_the_ledger`, `clear_the_road_toughs`). **True failure.** The extractor ignores the deduplication rule ("DO NOT emit an objective if its current state... already matches"). Remediation: Strengthen prompt to only emit the specific objective index that changed, or omit the quest entirely if all objectives are already done.
3. **`universal.narrate.pressure_directive_rendered` (T5,11):** Immediate pressure present but no Pressure/Overwhelm directive. **True failure.** The rules pipeline sets stakes, but the engine fails to map immediate scene pressure to a narration directive. Remediation: Add a data-flow step that injects `Narration Directive: Pressure` when `scene_pressure` contains `urgency: immediate`.
4. **`universal.progress.actions_quality` (T12):** Actions has 0 entries. **True failure.** Progress extractor failed to emit the required 4 actions. Remediation: Add a hard validation rule in the prompt: "You MUST emit exactly 4 actions. If uncertain, generate plausible options based on current stakes."
5. **Parse Error T13 (`gm_beat.type`):** Input `'environmental'` rejected. **True failure.** Progress extractor confused `type` and `surface_as` fields. Remediation: Clarify schema in prompt: `type` accepts `[complication, revelation, ...]`. `surface_as` accepts `[ambient, event, ...]`. Add explicit warning: "Do not swap type and surface_as."

---

# SECTION 7 — Per-Pipeline Mechanical Critique

### Rules Pipeline
**What Went Well:** Correctly distinguishes no-roll vs roll turns. Handles payment exception rule flawlessly. Intent classification is generally accurate for social interactions.
**What Went Poorly:** Misclassifies physical actions as `sneak`/`deceive` (T8, T11). Fails to map `tackle` to `strength`/`dexterity` or `climb`.
**Prompt Adherence Failures:** None structural, but behavioral drift on `intent_verb` mapping.
**Mechanic Ownership Check:** Correct.
**Scope Discipline:** Correct.
**Issues Bulleted List:**
- `- **Intent verb misclassification** (turns: 8, 9, 11) — Failure mode: scope/domain mismatch. Remediation: Add explicit few-shot examples mapping physical verbs (`tackle`, `unlock`, `push`) to `strength`/`dexterity`/`climb`, not `sneak`/`deceive`.
**Pipeline Score: 4**

### Narrate Pipeline
**What Went Well:** Prose quality is high, adheres to pack style, correctly integrates GM beats and directives. Handles fail-band outcomes properly.
**What Went Poorly:** None significant. Occasionally verbose, but within budget.
**Prompt Adherence Failures:** None.
**Mechanic Ownership Check:** Correct.
**Scope Discipline:** Correct.
**Issues Bulleted List:** None.
**Pipeline Score: 4**

### Extract Scene Pipeline
**What Went Well:** Excellent NPC grounding. Correctly handles location changes and scene tags. Deduplication works well.
**What Went Poorly:** None significant.
**Prompt Adherence Failures:** None.
**Mechanic Ownership Check:** Correct.
**Scope Discipline:** Correct.
**Issues Bulleted List:** None.
**Pipeline Score: 4**

### Extract State Pipeline
**What Went Well:** Handles spending/giving rule well. Condition TTL guidance is followed.
**What Went Poorly:** Ignores explicit narration numbers (T5: says 200, extracts 1). Hallucinates item removal on failed use (T8: `brass_key` removed despite failed unlock).
**Prompt Adherence Failures:** Violates "Priority 1 — Explicit numbers" (T5). Violates "State-presence rule" (T8).
**Mechanic Ownership Check:** Correct.
**Scope Discipline:** Correct.
**Issues Bulleted List:**
- `- **Amount extraction failure** (turn: 5) — Failure mode: failed to output key information. Remediation: Add explicit negative example: "Narration: 'drop 200 credits' → extract 200. Never substitute."`
- `- **Phantom item removal** (turn: 8) — Failure mode: messy logic. Remediation: Clarify that failed use/insertion does not trigger `inventory_remove`. Only consumption, spending, or explicit loss does.`
**Pipeline Score: 3**

### Extract Progress Pipeline
**What Went Well:** Quest deduplication works for active objectives. Recent events tracking is accurate. Action suggestions are generally relevant.
**What Went Poorly:** Over-generates GM beats every turn (always `replace`). Re-emits completed quests (T2, T7, T12). Confuses `type`/`surface_as` schema (T13). Missing actions (T12).
**Prompt Adherence Failures:** Violates GM Beat sparsity directive (T9-T13). Violates Quest deduplication rule (T2, T7, T12). Violates schema literal constraints (T13).
**Mechanic Ownership Check:** Correct.
**Scope Discipline:** Correct.
**Issues Bulleted List:**
- `- **GM Beat overgeneration** (turns: 9-13) — Failure mode: bad prompt. Remediation: Rewrite disposition tree to explicitly reward `carry`/`null`. Add: "If the previous beat was narrated and remains relevant, emit `beat_disposition: carry` and `gm_beat: null`. Do not generate new beats every turn."`
- `- **Quest deduplication failure** (turns: 2, 7, 12) — Failure mode: failed to output key information. Remediation: Add hard rule: "If quest status is `completed`, omit `quest_updates` entirely. Only emit the specific objective index that changed."`
- `- **Schema field confusion** (turn: 13) — Failure mode: schema drift. Remediation: Explicitly separate `type` and `surface_as` in schema examples. Add warning: "Do not swap fields."`
**Pipeline Score: 2**

---

# SECTION 8 — Cross-Pipeline Correlation

**Rules → Narrate Binding:** Roll bands and directives correctly shape narrator prose register. Fail-band outcomes are respected.
**Rules → Extract State Routing:** Stakes are named in rules, and mechanical consequences are extracted when bands are setbacks/fails. Works.
**Narrate → Scene Extract Consistency:** NPC enter/exit and location changes are narrated first, then captured by scene extractor. Handoff is clean.
**Narrate → State Extract Consistency:** Inventory changes are mostly captured. T5 amount mismatch and T8 phantom removal break consistency.
**Narrate → Progress Extract Consistency:** Quest objectives are advanced correctly. T12 re-emission of completed quest breaks consistency.
**Progress → Narrate Feedback Loop:** GM beats surface correctly in narration, but the disposition loop is broken (always `replace`). Recent events feed rules context appropriately.

---

# SECTION 9 — Storytelling Criteria (SECONDARY)

**quest_arc_quality:** Quests form a compelling, earned arc. `settle_the_debt` resolves T2, `deliver_the_ledger` resolves T7, `clear_the_road_toughs` resolves T12. Completion creates observable story consequences (credits, new contracts, chase).
**rewards_and_consequences [trace]:** Successes yield credits and quest progression. Failures yield immediate pressure and chase mechanics. The pattern is consistent and rewarding.
**world_consistency:** All entities in narration are sanctioned by the engine, worldpack, or player input. No unsanctioned introductions.
**failure_arc [trace]:** Failures create interesting options rather than dead ends. T5 setback leads to a bribe opportunity. T10 partial leads to a tense standoff. T12 setback leads to a chase. Mechanics actively shape future turns.

---

# SECTION 10 — Verdicts

**V1 — Mechanical Integrity → 3/5**
Extraction misses (T5, T8) and progress pipeline failures (beat overgeneration, quest dedup collisions, schema confusion) cap the score. The rules and scene pipelines are strong, but progress and state require prompt tightening.

**V2 — Narrative Quality → 4/5**
Prose is strong, tone matches dice bands, and GM beats are woven in naturally. The narrator follows directives well. Minor verbosity does not detract significantly.

**V3 — System Cohesion → 3/5**
Pipeline handoffs work, but the progress extractor's beat overgeneration and quest re-emission create state noise. The engine behaves as four strong pipelines and one struggling one.

**V4 — Prompt Quality → 3/5**
Rules, Narrate, and Scene prompts are well-structured. Progress prompt needs significant revision on beat disposition and quest deduplication. State prompt needs explicit number priority reinforcement.

**V5 — Compaction → 2/5**
Chronicle bullets are accurate, but the compactor completely fails to sanitize inventory, quests, pressures, or conditions. It only updates history and events, ignoring 80% of its promised capabilities.

---

# SECTION 11 — Trace Quality and Eval Self-Assessment

### 11A — Input Sufficiency
| Data Category | Rating | Notes |
|---|---|---|
| System prompts (all 5 pipelines) | SUFFICIENT | Complete and correctly attributed. |
| Per-turn user prompts (all 5 pipelines) | SUFFICIENT | Fully visible. |
| Per-turn engine outputs | SUFFICIENT | Complete JSON and prose. |
| State snapshots (per turn) | SUFFICIENT | Full diffs provided. |
| Applied/rejected deltas | SUFFICIENT | Detailed enough to verify. |
| Context telemetry | SUFFICIENT | Token counts and trim status visible. |
| Static context | SUFFICIENT | Complete. |
| Compaction signals | SUFFICIENT | Events correctly identified. |
| Auto-checker signals | SUFFICIENT | Clearly attributed. |

### 11B — Missing Data
- None. The trace provided all necessary data for evaluation.

### 11C — Questions You Could Not Answer
- None. All criteria were fully assessable.

### 11D — Trace Structure Suggestions
1. **Most useful section:** Deterministic Signals (Auto-Checker Failures & Metrics). Provides authoritative grounding for mechanical evaluation.
2. **Least useful section:** Compaction Features. The trace shows `Applied sanitization actions: (none recorded)`, which is unhelpful for debugging the compactor's internal logic.
3. **One piece of data to add:** Compactor internal logs or decision traces for sanitization steps. Knowing *why* sanitization was skipped would accelerate remediation.
4. **Compaction signal reliability:** Reliable. Events fired at T6 and T12 as expected.

---

# SECTION 12 — Actionable Issues

**Critical:**
- `- **GM Beat schema field confusion** (turn: 13) — Failure mode: schema drift. Remediation: Explicitly separate `type` and `surface_as` in the progress system prompt. Add validation warning: "Do not swap fields. `type` accepts `[complication, revelation, ...]`. `surface_as` accepts `[ambient, event, ...]`."`

**Major:**
- `- **GM Beat overgeneration** (turns: 9-13) — Failure mode: bad prompt. Remediation: Rewrite the disposition tree to explicitly reward `carry`/`null`. Add: "If the previous beat was narrated and remains relevant, emit `beat_disposition: carry` and `gm_beat: null`. Do not generate new beats every turn."`
- `- **Quest deduplication failure** (turns: 2, 7, 12) — Failure mode: failed to output key information. Remediation: Add hard rule: "If quest status is `completed`, omit `quest_updates` entirely. Only emit the specific objective index that changed."`
- `- **State extractor amount mismatch** (turn: 5) — Failure mode: failed to output key information. Remediation: Add explicit negative example: "Narration: 'drop 200 credits' → extract 200. Never substitute."`

**Minor:**
- `- **Phantom item removal** (turn: 8) — Failure mode: messy logic. Remediation: Clarify that failed use/insertion does not trigger `inventory_remove`. Only consumption, spending, or explicit loss does.`
- `- **Rules intent verb misclassification** (turns: 8, 9, 11) — Failure mode: scope/domain mismatch. Remediation: Add explicit few-shot examples mapping physical verbs (`tackle`, `unlock`, `push`) to `strength`/`dexterity`/`climb`, not `sneak`/`deceive`.`
- `- **Auto-checker false positives** (turns: 1,2,3,5,6,7,12) — Failure mode: noisy signals. Remediation: Fix checker regex to exclude location IDs, item names, and common adverbs from NPC extraction checks.`