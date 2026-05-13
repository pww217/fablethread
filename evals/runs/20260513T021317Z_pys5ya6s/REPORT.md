# Eval Report — `full_cycle`

**Pack:** `eval-pack` · **Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8` · **Temp override:** `None`  
**Started:** 2026-05-13T02:13:17.561731+00:00 · **Finished:** 2026-05-13T02:20:29.312652+00:00  
**Output dir:** `/Users/pwilson/Repos/ccya/evals/runs/20260513T021317Z_pys5ya6s`  
**Compared against:** `/Users/pwilson/Repos/ccya/evals/runs/20260512T154142Z_uufm2ojg/artifacts`

## Judge Summary

**Mechanical:** 3/5  
**Narrative:** 4/5  
**System Cohesion:** 3/5  
**Prompt Quality:** 3/5  
**Compaction:** 2/5  
**State Fidelity:** 75.0%  
**Prompt Adherence:** 70.0%
**Rubric:** `/Users/pwilson/Repos/ccya/evals/rubrics/default.md`
**Judge model:** `mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit`

**Pipeline scores:**
- rules: 4/5
- narrate: 4/5
- extract_scene: 4/5
- extract_state: 3/5
- extract_progress: 2/5

**Trace:** [`full_cycle.trace.md`](full_cycle.trace.md)
**Judge response:** [`full_cycle.judge.md`](full_cycle.judge.md)

## ⚠️  Flagged

### `extraction_retries` — 1 retried extraction stream(s)

- turn 13 `extraction.progress` attempts=2


## Judge Verdict (full)

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

## Auto-Checker

**238 passed, 22 failed**

| Turn | Assertion | Result | Detail |
|---|---|---|---|
| 1 | `rules.rolled` | ✅ | rolled=False |
| 1 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 1 | `universal.pending_gm_beat.consumed` | ✅ | (first turn) |
| 1 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 1 | `universal.location_change.applied` | ✅ | (no change) |
| 1 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 1 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
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
| 2 | `extract.state.inventory_remove` | ✅ | inventory_remove[credits] amount=500 |
| 2 | `extract.progress.quest_updates` | ✅ | quest_updates[settle_the_debt] found |
| 2 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 2 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 2 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 2 | `universal.location_change.applied` | ✅ | (no change) |
| 2 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 2 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Slowly'] |
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
| 3 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 3 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 3 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 3 | `universal.location_change.applied` | ✅ | marrows_crossing -> marrows_crossing_streets |
| 3 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 3 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 3 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
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
| 4 | `universal.location_change.applied` | ✅ | marrows_crossing_streets -> merchant_road_outskirts |
| 4 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 4 | `universal.npc_mention.extracted` | ✅ | 4 candidates skipped (likely locations/items, not NPCs) |
| 4 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
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
| 5 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 5 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 5 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 5 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 5 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 5 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 5 | `universal.inventory.no_overdraw` | ✅ | checked 1 removes |
| 5 | `universal.pressure.immediate_cap` | ✅ | 1 immediate |
| 5 | `universal.narrate.pressure_directive_rendered` | ❌ | 1 immediate pressures but no Pressure/Overwhelm directive in narrate user prompt |
| 5 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 5 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 5 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 5 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 6 | `rules.rolled` | ✅ | rolled=True |
| 6 | `extract.state.inventory_remove` | ❌ | inventory_remove[credits] amount=20 |
| 6 | `extract.progress.quest_updates` | ✅ | quest_updates[clear_the_road_toughs] found |
| 6 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 6 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 6 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 6 | `universal.location_change.applied` | ✅ | (no change) |
| 6 | `universal.narrate.binding_present` | ✅ | no roll required, binding not expected |
| 6 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 6 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 6 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
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
| 7 | `extract.progress.quest_updates` | ✅ | quest_updates[deliver_the_ledger] found |
| 7 | `extract.progress.quest_status` | ❌ | quest[deliver_the_ledger].status='active' (expected 'completed') |
| 7 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 7 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 7 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 7 | `universal.location_change.applied` | ✅ | merchant_road_outskirts -> crossed_keys_inn |
| 7 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 7 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Ledger'] |
| 7 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 7 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
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
| 8 | `extract.state.inventory_remove` | ❌ | inventory_remove[brass_key] not found |
| 8 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 8 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 8 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 8 | `universal.location_change.applied` | ✅ | (no change) |
| 8 | `universal.narrate.binding_present` | ✅ | no roll required, binding not expected |
| 8 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 8 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 8 | `universal.scene.npc_cap` | ✅ | 0 NPCs |
| 8 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 8 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 8 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 8 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 8 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 8 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 8 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 8 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 8 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 8 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 9 | `rules.rolled` | ❌ | rolled=False |
| 9 | `extract.scene.scene_tags` | ❌ | scene_tags[social] not found |
| 9 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=9 |
| 9 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 9 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 9 | `universal.location_change.applied` | ✅ | (no change) |
| 9 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 9 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 9 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 9 | `universal.scene.npc_cap` | ✅ | 6 NPCs |
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
| 10 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 10 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 10 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 10 | `universal.location_change.applied` | ✅ | (no change) |
| 10 | `universal.narrate.binding_present` | ✅ | no roll required, binding not expected |
| 10 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 10 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 10 | `universal.scene.npc_cap` | ✅ | 6 NPCs |
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
| 11 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 11 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 11 | `universal.scene.npc_cap` | ✅ | 6 NPCs |
| 11 | `universal.pc.condition_no_dupes` | ✅ | 3 conditions, no dupes |
| 11 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 11 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 11 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 11 | `universal.pressure.immediate_cap` | ✅ | 1 immediate |
| 11 | `universal.narrate.pressure_directive_rendered` | ❌ | 1 immediate pressures but no Pressure/Overwhelm directive in narrate user prompt |
| 11 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 11 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 11 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 11 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 12 | `rules.rolled` | ✅ | rolled=False |
| 12 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 12 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 12 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 12 | `universal.location_change.applied` | ✅ | (no change) |
| 12 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 12 | `universal.npc_mention.extracted` | ✅ | (no narration) |
| 12 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 12 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 12 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 12 | `universal.progress.actions_quality` | ❌ | actions has 0 entries (expected 4) |
| 12 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 12 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 12 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 12 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 12 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 12 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 12 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 12 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 13 | `rules.rolled` | ❌ | rolled=True |
| 13 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=12 |
| 13 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 13 | `universal.pending_gm_beat.disposition_respected` | ✅ | (no disposition emitted) |
| 13 | `universal.location_change.applied` | ✅ | alleyway_near_inn -> river_docks |
| 13 | `universal.narrate.binding_present` | ✅ | no roll required, binding not expected |
| 13 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Ahead'] |
| 13 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 13 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 13 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 13 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 13 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 13 | `universal.inventory.no_overdraw` | ✅ | checked 0 removes |
| 13 | `universal.pressure.immediate_cap` | ✅ | 0 immediate |
| 13 | `universal.narrate.pressure_directive_rendered` | ✅ | (no immediates) |
| 13 | `universal.pressure.no_stale_immediate` | ✅ | no stale immediates |
| 13 | `universal.pacing.floor_no_relief` | ✅ | floor_count=0 |
| 13 | `universal.inventory.key_consumed` | ✅ | no key-use language |
| 13 | `universal.inventory.no_negative_amount` | ✅ | no negative amounts |
| 13 | `progress.quest_id_collision` | ❌ | quest_updates re-creates already-completed quest id='clear_the_road_toughs' |

## Universal Assert Results

| Assertion | Severity | Turns Failed | Turns Checked | First Failure Turn |
|---|---|---:|---:|---:|
| `extract.progress.quest_status` | 🔴 | 1 | 1 | T7 |
| `extract.progress.quest_updates` | 🔴 | 0 | 4 | — |
| `extract.scene.scene_tags` | 🔴 | 2 | 3 | T5 |
| `extract.state.inventory_remove` | 🔴 | 2 | 3 | T6 |
| `progress.quest_id_collision` | 🔴 | 3 | 3 | T2 |
| `rules.rolled` | 🔴 | 4 | 12 | T2 |
| `universal.inventory.key_consumed` | 🟡 | 0 | 13 | — |
| `universal.inventory.no_negative_amount` | 🔴 | 0 | 13 | — |
| `universal.inventory.no_overdraw` | 🔴 | 0 | 13 | — |
| `universal.location_change.applied` | 🔴 | 0 | 13 | — |
| `universal.momentum.band_delta` | 🔴 | 0 | 13 | — |
| `universal.narrate.binding_present` | 🔴 | 0 | 13 | — |
| `universal.narrate.pressure_directive_rendered` | 🔴 | 2 | 13 | T5 |
| `universal.npc_mention.extracted` | 🔴 | 7 | 13 | T1 |
| `universal.pacing.floor_no_relief` | 🟡 | 0 | 13 | — |
| `universal.pc.condition_no_dupes` | 🔴 | 0 | 13 | — |
| `universal.pending_gm_beat.consumed` | 🔴 | 0 | 13 | — |
| `universal.pending_gm_beat.disposition_respected` | 🔴 | 0 | 13 | — |
| `universal.pressure.immediate_cap` | 🔴 | 0 | 13 | — |
| `universal.pressure.no_stale_immediate` | 🟡 | 0 | 13 | — |
| `universal.progress.actions_quality` | 🔴 | 1 | 13 | T12 |
| `universal.recent_events.ring_bounded` | 🔴 | 0 | 13 | — |
| `universal.recent_events_add.turn_stamped` | 🔴 | 0 | 13 | — |
| `universal.scene.npc_cap` | 🔴 | 0 | 13 | — |

## Pacing Metrics

### Pressure Duration

| Pressure ID | First Turn | Last Turn | Duration (turns) | Flagged |
|---|---|---:|---:|---|
| `inn_entrance_blockade` | T5 | T5 | 1 |  |
| `toughs_closing_in` | T11 | T11 | 1 |  |

### Location Dwell

| Location ID | Turns Active | Flagged |
|---|---:|---|
| `alleyway_near_inn` | 1 |  |
| `crossed_keys_inn` | 5 | ⚠️ >4 turns |
| `marrows_crossing` | 2 |  |
| `marrows_crossing_streets` | 1 |  |
| `merchant_road_outskirts` | 3 |  |
| `river_docks` | 1 |  |

### Condition Duration

| Condition ID | First Turn | Last Turn | Duration (turns) | Flagged |
|---|---|---:|---:|---|
| `bruised_ribs` | T1 | T12 | 12 | ⚠️ >6 turns |
| `exhausted` | T13 | T13 | 1 |  |
| `low_morale` | T1 | T13 | 13 | ⚠️ >6 turns |
| `winded` | T11 | T11 | 1 |  |

## Turn Metrics

| # | input | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | retries | parse_fail | duration_s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | Walk over to Caron's table and sit down across f… | 1583 (+180) | 3441 (+186) | 2924 (+165) | 3568 (+145) | 4620 (+250) | 0 | 0 | 31.94 |
| 2 | I slide 500 credits across the table to Caron an… | 1874 (+153) | 3710 (+293) | 3247 (+147) | 3622 (+118) | 4671 (-13) | 0 | 0 | 26.10 |
| 3 | I find Halden by the town well and offer to carr… | 1934 (+132) | 3993 (+141) | 3319 (+155) | 3618 (+181) | 4625 (-111) | 0 | 0 | 29.10 |
| 4 | I leave Marrow's Crossing by the east gate and h… | 1889 (+156) | 4298 (+239) | 3182 (+218) | 3547 (+152) | 4418 (-91) | 0 | 0 | 27.18 |
| 5 | I walk up to the two toughs at the inn door and … | 1777 (+138) | 4263 (+104) | 3157 (+174) | 3669 (+104) | 4521 (-201) | 0 | 0 | 34.70 |
| 6 | I drop 200 credits on the ground between the tou… | 1967 (+87) | 4437 (+87) | 3328 (+114) | 3595 (+118) | 4681 (-210) | 0 | 0 | 40.13 |
| 7 | I sit across from Halden at his table, slide the… | 1892 (+104) | 4458 (+94) | 3278 (+111) | 3610 (+122) | 4577 (-153) | 0 | 0 | 32.23 |
| 8 | I pull out the brass key Halden gave me and try … | 1921 (+144) | 4467 (+7) | 3274 (+282) | 3549 (+215) | 4542 (-37) | 0 | 0 | 29.11 |
| 9 | I press my ear against the inn's stone wall and … | 1798 (+153) | 4339 (+217) | 3050 (+125) | 3524 (+95) | 4292 (-189) | 0 | 0 | 26.56 |
| 10 | I approach Matthew Estrada at the bar, grab his … | 1828 (+83) | 4419 (+83) | 3320 (+252) | 3645 (+174) | 4813 (+76) | 0 | 0 | 30.76 |
| 11 | Matthew's bodyguard draws a knife! I tackle him … | 1977 (+147) | 4496 (+132) | 3368 (+178) | 3535 (+134) | 4742 (-35) | 0 | 0 | 33.27 |
| 12 |  | — | — | 0 (-3062) | 0 (-3362) | 0 (-4792) | 0 | 0 | 50.57 |
| 12 | I grab the ledger from my coat and sprint out th… | 1885 (+264) | 4558 (+241) | 3317 (+452) | 3623 (+133) | 4848 (+425) | 0 | 0 | 40.01 |
| 13 | I find a quiet corner at the dock and wrap my wo… | 1873 | 4576 | 3216 | 3632 | 4657 | 1 | 0 | 0.00 |
|  | TOTALS | 24198 | 55455 | 41980 | 46737 | 60007 | 1 | 0 | 431.68 |

**Total turns:** 14 · **Total duration:** 431.68s · **Avg/turn:** 30.83s
**Total tokens in:** 228,377 · **Total tokens out:** 12,821 · **Total LLM time:** 407.4s
**Total retries:** 1 · **Total parse failures:** 0


## Warnings (≥ warn threshold but < fail threshold)

- `rules` turn 1: 1403 → 1583 (+12.8%)
- `rules` turn 12: 1621 → 1885 (+16.3%)
- `extraction.scene` turn 12: 2865 → 3317 (+15.8%)
