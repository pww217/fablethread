# Eval Report — `full_cycle`

**Pack:** `eval-pack` · **Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8` · **Temp override:** `None`  
**Started:** 2026-05-11T18:50:20.940226+00:00 · **Finished:** 2026-05-11T18:57:49.664759+00:00  
**Output dir:** `/Users/pwilson/Repos/ccya/evals/runs/20260511T185020Z_5mrnmm7j`  
**Compared against:** `/Users/pwilson/Repos/ccya/evals/runs/20260511T162447Z_neevpjy5/artifacts`

## Judge Summary

**Mechanical:** 2/5  
**Narrative:** 3/5  
**System Cohesion:** 3/5  
**Prompt Quality:** 3/5  
**Compaction:** 2/5  
**State Fidelity:** 77.0%  
**Prompt Adherence:** 95.0%
**Rubric:** `/Users/pwilson/Repos/ccya/evals/rubrics/default.md`
**Judge model:** `mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit`

**Pipeline scores:**
- rules: 4/5
- narrate: 2/5
- extract_scene: 4/5
- extract_state: 2/5
- extract_progress: 4/5

**Trace:** [`full_cycle.trace.md`](full_cycle.trace.md)
**Judge response:** [`full_cycle.judge.md`](full_cycle.judge.md)

## ⚠️  Flagged

### `rejected_deltas` — 3 rejected delta(s) across the run

- turn 6: 1 rejected
- turn 9: 1 rejected
- turn 13: 1 rejected

## Other observations

- **`runner_errors`**: 3 turn(s) errored
- turn 6: engine_errors: [{"trace_id": "b3c5c507", "message": "Delta validation failed (1 rejection(s))."}]
- turn 9: engine_errors: [{"trace_id": "38285a62", "message": "Delta validation failed (1 rejection(s))."}]
- turn 13: engine_errors: [{"trace_id": "80554f84", "message": "Delta validation failed (1 rejection(s))."}]


## Judge Verdict (full)

# SECTION 1 — Mechanic Lifecycle Tables

### 1A — Momentum Table

| Turn | Roll Band | Δ Momentum | Band Before→After | Tone Match? | Flag |
|------|-----------|------------|-------------------|-------------|------|
| 1 | fail | -1 | 0→-1 | Yes | — |
| 2 | none | 0 | -1→-1 | Yes | — |
| 3 | partial | 0 | -1→-1 | Yes | — |
| 4 | none | 0 | -1→-1 | Yes | — |
| 5 | crit_success | +2 | -1→1 | Yes | — |
| 6 | setback | -1 | 1→0 | Yes | — |
| 7 | partial | 0 | 0→0 | Yes | — |
| 8 | setback | -1 | 0→-1 | Yes | — |
| 9 | success | +1 | -1→0 | Yes | — |
| 10 | fail | -1 | 0→-1 | Yes | — |
| 11 | fail | -1 | -1→-2 | Yes | — |
| 12 | partial | 0 | -2→-2 | Yes | — |
| 13 | none | 0 | -2→-2 | Yes | — |

Momentum responds correctly to dice. Band progression feels appropriate, tracking the player's struggle and brief successes.

### 1B — GM Beat Table

| Generated (Tn) | Beat Type | Surfaced (Tm) | Surface Lag (turns) | Effect | Flag |
|----------------|-----------|---------------|---------------------|--------|------|
| 5 | revelation | 5 | 0 | Toughs reveal employer | — |
| 6 | escalation | 6 | 0 | Toughs target ledger | — |
| 7 | pressure | 7 | 0 | Guard footsteps heard | — |
| 8 | pressure | 8 | 0 | Guards approach | — |
| 9 | pressure | 9 | 0 | Guards enter street | — |
| 10 | complication | 10 | 0 | Guards question patrons | — |
| 11 | pressure | 11 | 0 | Guards detain player | — |
| 12 | pressure | 12 | 0 | Muddy paths hinder chase | — |

Beats generate at appropriate frequency. Types are varied and consistently shape the next turn's atmosphere.

### 1C — Scene Pressure Table

| ID | Added (Tn) | Urgency | Escalated? | Resolved (Tm) | Lifespan (turns) | Flag |
|----|------------|---------|------------|---------------|-----------------|------|
| caron_debt_escalation | 1 | immediate | No | 2 | 1 | — |
| town_guard_threat | 7 | building | Yes (T8) | 10 | 3 | — |
| guard_arrival_imminent | 8 | immediate | No | 10 | 2 | — |
| guard_intervention_tension | 10 | immediate | No | 11 | 1 | — |
| guard_arrest_threat | 11 | immediate | No | 12 | 1 | — |
| guard_chase_pressure | 12 | immediate | No | 13 | 1 | — |
| guard_search_docks | 13 | building | No | — | 1 | UNRESOLVED_AT_END |

Pressures escalate and resolve cleanly. `guard_search_docks` is unresolved at run end but only 1 turn old. No inert pressures.

### 1D — Condition Lifecycle Table

| ID | Added (Tn) | Source | Still Present (Tm) | Resolved | Duration (turns) | Flag |
|----|------------|--------|--------------------|----------|-----------------|------|
| bruised_ribs | seed | engine | No (T13) | 13 | 13 | OVERLONG |
| low_morale | seed | engine | Yes | — | 13 | — |
| shaken | 10 | narrative | No (T11) | 11 | 1 | — |

`bruised_ribs` persists for 13 turns. Narration at T13 still references "stinging protest of your bruised ribs" and "bloodied bandages" after the extractor removes it. Flag: `SILENT_DROP` / `NARRATION_DRIFT`.

### 1E — Quest Arc Table

| Quest ID | Created (Tn) | Objectives | Objectives Done | Resolved (Tm) | Outcome | Flag |
|----------|--------------|------------|-----------------|---------------|---------|------|
| settle_the_debt | seed | 2 | 2 | 2 | completed | — |
| deliver_the_ledger | seed | 3 | 2 | — | active | — |
| clear_the_road_toughs | seed | 2 | 1 | — | active | — |

Quest arcs pace well. `settle_the_debt` completes cleanly. `deliver_the_ledger` and `clear_the_road_toughs` advance logically.

### 1F — Inventory Evolution Table

| Turn | Action | Item | Qty | Narration Reflected? | Extracted? | Flag |
|------|--------|------|-----|---------------------|------------|------|
| 2 | remove | credits | 500 | Yes | Yes | — |
| 3 | add | ledger | 1 | Yes | Yes | — |
| 6 | remove | credits | 200 | Yes | No (Rejected) | SPENDING_MISS |
| 9 | remove | credits | 1 | Yes | No (Rejected) | SPENDING_MISS |
| 11 | add | iron_key | 1 | Yes | Yes | — |
| 13 | remove | bandages | 1 | Yes | No (Drift) | AMOUNT_MISMATCH |
| 13 | remove | credits | 5 | Yes | No (Rejected) | SPENDING_MISS |

Critical failure on `credits` spending from T6 onward. Narrator invents spending events; extractor attempts removal; engine rejects due to 0-stack. `bandages` amount drifts (state shows 3, should be 2).

---

# SECTION 2 — State Fidelity

### 2A — State Coherence
State evolves logically except for the `credits` and `bandages` domains. Inventory and conditions agree with each other, but `credits` spending attempts from T6-T13 create a persistent mismatch: narration describes spending, state shows 0, and deltas are rejected. Conditions track correctly except `bruised_ribs` removal at T13 contradicts T13 narration.

### 2B — State Drift
- **Extraction drift:** `credits` remove deltas at T6, T9, T13 fail validation. `bandages` remove at T13 extracts 1, but state snapshot shows amount 3 (should be 2).
- **Narration drift:** T13 narration says "pulling out your Linen bandages to wrap tightly" and "bloodied bandages" after `bruised_ribs` was removed. T6/T9/T13 narration describes spending credits that don't exist.

### 2C — State Completeness
`extract_state` fails to update `credits` and `bandages` due to validation rejections. `extract_scene` correctly updates `present_npcs` and `location`. `extract_progress` correctly updates `recent_events` and `scene_pressure`.

### 2D — State Fidelity Rate Calculation
Turns with no rejected deltas AND no detected drift: T1, T2, T3, T4, T5, T7, T8, T10, T11, T12. (10 turns)
Total turns: 13.
Rate: 10 / 13 = 0.77.

---

# SECTION 3 — Prompt Quality Audit

### 3A — Rules Pipeline Prompt Audit

| Criterion | Score | Evidence (turn + quote) |
|-----------|-------|-------------------------|
| P1 | Y | System static, user turn-variable. |
| P2 | Y | Matches architecture diagram. |
| P3 | PARTIAL | `present_npcs` block duplicated in rules/narrate prompts. |
| P4 | Y | Schema and guidance distinct. |
| P5 | Y | No contradictions. |
| P6 | Y | Terse. |
| P7 | Y | JSON schema clear. |
| P8 | PARTIAL | `intent_verb` drift at T11 (`sneak` for tackle/search). |
| P9 | N | Few-shot not needed for intent classification. |

**Remediation summary:**
- Add few-shot examples for `intent_verb` mapping when player input mixes physical and social actions (T11).

### 3B — Narrate Pipeline Prompt Audit

| Criterion | Score | Evidence (turn + quote) |
|-----------|-------|-------------------------|
| P1 | Y | System static, user turn-variable. |
| P2 | Y | Matches architecture. |
| P3 | PARTIAL | `present_npcs` duplicated. |
| P4 | Y | Schema/guidance distinct. |
| P5 | Y | No contradictions. |
| P6 | Y | Terse. |
| P7 | Y | Clear formatting. |
| P8 | FAIL | Ignores "Player input is truth" rule at T7, T9, T11. |
| P9 | Y | Needs examples for handling impossible/absurd inputs pragmatically. |

**Remediation summary:**
- Strengthen "Player input is truth" rule with explicit negative constraint: "NEVER replace player input with a different action. If input is absurd, narrate the attempt failing, not a different event."
- Add few-shot for pragmatic interpretation of impossible actions.

### 3C — Extract Scene Pipeline Prompt Audit

| Criterion | Score | Evidence (turn + quote) |
|-----------|-------|-------------------------|
| P1 | Y | |
| P2 | Y | |
| P3 | PARTIAL | `present_npcs` duplicated. |
| P4 | Y | |
| P5 | Y | |
| P6 | Y | |
| P7 | Y | |
| P8 | Y | |
| P9 | N | |

**Remediation summary:** None critical. Scene extraction adheres well.

### 3D — Extract State Pipeline Prompt Audit

| Criterion | Score | Evidence (turn + quote) |
|-----------|-------|-------------------------|
| P1 | Y | |
| P2 | Y | |
| P3 | PARTIAL | `present_npcs` duplicated. |
| P4 | Y | |
| P5 | Y | |
| P6 | Y | |
| P7 | Y | |
| P8 | FAIL | Violates spending/giving rule at T6, T9, T13. |
| P9 | Y | Needs example for 0-stack spending. |

**Remediation summary:**
- Add explicit rule: "If narration describes spending an item not in inventory, emit NO `inventory_remove`. Do not invent phantom spends. Omit delta entirely."
- Add few-shot for handling spending attempts on depleted stacks.

### 3E — Extract Progress Pipeline Prompt Audit

| Criterion | Score | Evidence (turn + quote) |
|-----------|-------|-------------------------|
| P1 | Y | |
| P2 | Y | |
| P3 | PARTIAL | `present_npcs` duplicated. |
| P4 | Y | |
| P5 | Y | |
| P6 | Y | |
| P7 | Y | |
| P8 | Y | |
| P9 | N | |

**Remediation summary:** None critical. Progress extraction adheres well.

### 3F — Prompt Adherence Rate Calculation
Rules: 13/13 PASS. Narrate: 10/13 PASS. Scene: 13/13 PASS. State: 13/13 PASS. Progress: 13/13 PASS.
Total: 62 / 65 = 0.95.

### 3G — Cross-Pipeline Redundancy Summary
- `present_npcs` block appears verbatim in Rules, Narrate, Scene, State, and Progress prompts. This is intentional for grounding but wastes ~150 tokens/turn.
- **Top 3 dedup opportunities:**
  1. Pass `present_npcs` as a compacted JSON array to Rules/Narrate instead of full text blocks.
  2. Use a shared `scene_context` template injected at runtime rather than duplicating in every user prompt.
  3. Trim `known_characters` in Progress/Scene prompts to only IDs and titles, not full bios.

---

# SECTION 4 — Mechanic Interplay Assessment

### 4A — Beat→Narrative Loop
Tight. Beats consistently shape the next turn's atmosphere and NPC behavior. No orphaned beats.

### 4B — Momentum→Directive→Tone Chain
Tight. Band outcomes directly shape narrator prose register. Low momentum (-2) at T11-T12 correctly yields desperate, frantic prose.

### 4C — Pressure→Stakes→Consequence Chain
Tight. `town_guard_threat` feeds into T8/T9 stakes. Setback at T6 correctly names "thugs refuse bribe" in stakes, which matches narration.

### 4D — Condition→Narrative Callback
`bruised_ribs` referenced T1-T12. Removed T13 but narration still references it. `low_morale` referenced T1. `shaken` referenced T10. Mostly tight, but T13 condition removal breaks callback.

### 4E — Pacing Assessment
High-tension from T5-T12. Pressure timers align well. Momentum arc: low → build → peak → resolution attempt. Beat variety good. Escape paths viable at T12.

### 4F — NPC Entry/Exit Coherence
T5 adds toughs. T10 removes toughs. T11 adds bodyguard. T12 removes bodyguard. T13 adds dock boy. All tracked correctly. No ghost NPCs.

### 4G — Player Intent Fidelity
**Loose.** T7 completely ignores input ("I sit across from Halden..."). T9 and T11 honor input but add system-injected failure traces. T13 honors input. Narrator priority rule violated at T7.

---

# SECTION 5 — Compaction Report

### 5A — Chronicle Quality
T6 bullets: Accurate. Covers T1-T3 named entities and quest outcomes.
T12 bullets: Accurate. Covers T4-T9 events, toughs, Calloway, guards.
No generic bullets. No entity inversions.

### 5B — Sanitization Fidelity
T6: `quest_close` missed (should close `settle_the_debt` at T2, but engine did it; compactor didn't log it). `pressure_remove` not logged.
T12: `pressure_remove` not logged. `condition_remove` not logged.
Score: `quest_close`: [NA], `condition_remove`: [FAIL], `pressure_remove`: [FAIL], `inventory_remove`: [NA], `recent_events_compact`: [OK].
Sanitization Fidelity Rate: 1 / 4 = 0.25.

### 5C — Compaction Score (1–5)
2. Bullets accurate, but sanitization logging entirely absent. Compactor fails to report applied sanitization actions.

---

# SECTION 6 — Auto-Checker Failures

1. `universal.npc_mention.extracted` (T2, T3, T4, T5, T7, T8, T9): Narration mentions "Finally", "Crossed", "Crossing". These are location names or adverbs, not NPCs. **False positive.** Recommend checker fix: exclude location names and common adverbs from NPC mention validation.
2. `progress.quest_id_collision` (T2): Extractor emits `settle_the_debt` with objectives done. Prompt mandates this for auto-close. **False positive.** Recommend checker fix: allow re-emission of completed quests when `done: true` for all objectives.

---

# SECTION 7 — Per-Pipeline Mechanical Critique

### Rules Pipeline
**What Went Well:** Correctly classifies intent and stakes. Handles compound actions well (T11).
**What Went Poorly:** `intent_verb` drift at T11 (`sneak` for tackle/search). Should be `attack` or `sneak` depending on gating action.
**Prompt Adherence Failures:** None this run.
**Mechanic Ownership Check:** Correct.
**Scope Discipline:** Correct. Only rolls when warranted.
**Issues Bulleted List:**
- `intent_verb` classification drift for mixed physical/social actions (turns: 11) — Failure mode: scope/domain mismatch. Remediation: Add few-shot examples for `intent_verb` selection when input contains multiple action types.
**Pipeline Score:** 4

### Narrate Pipeline
**What Went Well:** Strong prose, handles band directives and GM beats effectively. Good spatial clarity.
**What Went Poorly:** Ignores player input at T7. Fails "Player input is truth" rule.
**Prompt Adherence Failures:** T7: "Player input is truth (HIGHEST PRIORITY)" violated. Narrator wrote combat scene instead of player's requested ledger handoff.
**Mechanic Ownership Check:** Correct.
**Scope Discipline:** Correct.
**Issues Bulleted List:**
- Ignores player input priority rule (turns: 7) — Failure mode: bad prompt. Remediation: Add explicit negative constraint: "NEVER replace player input with a different action. If input conflicts with beat, narrate input FIRST, then integrate beat."
**Pipeline Score:** 2

### Extract Scene Pipeline
**What Went Well:** Accurate NPC tracking and location updates. Good compendium updates.
**What Went Poorly:** Adds `town_guards` as NPC at T5/T10. Acceptable but could be ambient.
**Prompt Adherence Failures:** None this run.
**Mechanic Ownership Check:** Correct.
**Scope Discipline:** Correct.
**Issues Bulleted List:** None critical.
**Pipeline Score:** 4

### Extract State Pipeline
**What Went Well:** Extracts conditions accurately. Handles location changes well.
**What Went Poorly:** Fails spending/giving rule at T6, T9, T13. Attempts to remove `credits` when stack is 0.
**Prompt Adherence Failures:** T6, T9, T13: "Spending/giving rule (MANDATORY)" violated. Extractor emits remove delta for non-existent item instead of omitting.
**Mechanic Ownership Check:** Correct.
**Scope Discipline:** Correct.
**Issues Bulleted List:**
- Fails spending rule on 0-stack items (turns: 6, 9, 13) — Failure mode: bad prompt. Remediation: Add explicit rule: "If narration describes spending an item not in inventory, emit NO `inventory_remove`. Do not invent phantom spends. Omit delta entirely."
**Pipeline Score:** 2

### Extract Progress Pipeline
**What Went Well:** Quest updates accurate. Recent events ring buffer managed well. Pressure lifecycle correct.
**What Went Poorly:** `clear_the_road_toughs` objective 2 not advanced at T11 despite combat. Minor pacing lag.
**Prompt Adherence Failures:** None this run.
**Mechanic Ownership Check:** Correct.
**Scope Discipline:** Correct.
**Issues Bulleted List:** None critical.
**Pipeline Score:** 4

---

# SECTION 8 — Cross-Pipeline Correlation

### Rules → Narrate Binding
Tight. Band/directive shapes prose register. T5 crit success yields respectful toughs. T6 setback yields greedy toughs.

### Rules → Extract State Routing
Tight. Stakes correctly named in rules, extracted in state. T6 setback stake matches narration.

### Narrate → Scene Extract Consistency
Tight. NPC enter/exit narrated → scene extract captures it. T5 toughs added. T10 toughs removed.

### Narrate → State Extract Consistency
Loose. Inventory change narrated → state extract attempts removal but fails validation. T6/T9/T13 credits spending.

### Narrate → Progress Extract Consistency
Tight. Quest objective narrated → progress extract updates it. T12 `deliver_the_ledger` obj 2 advanced.

### Progress → Narrate Feedback Loop
Tight. `gm_beat` from T-N surfaces in narration T-(N+1). `scene_pressure_add` feeds rules context.

---

# SECTION 9 — Storytelling Criteria (SECONDARY)

### quest_arc_quality
Quests form a compelling arc. `settle_the_debt` completes cleanly at T2. `deliver_the_ledger` and `clear_the_road_toughs` advance logically through player choices. Completion/failure feels earned.

### rewards_and_consequences
Successes produce positive outcomes (T5 crit success yields information). Failures produce lasting costs (T6 setback yields ledger targeting, T11 fail yields guard arrest threat). Mechanics drive narrative consequences effectively.

### world_consistency
All entities in narration sanctioned by engine, worldpack, or player input. No unsanctioned introductions. `James Calloway` and `town_guards` properly grounded.

### failure_arc
Failures create interesting options rather than dead ends. T6 setback leads to ledger targeting. T11 fail leads to guard arrest threat. T12 partial yields chase. Mechanics affect future turns appropriately.

---

# SECTION 10 — Verdicts

### V1 — Mechanical Integrity → 2
Critical extraction failures on `credits` spending (T6, T9, T13) and `bandages` amount drift (T13). Narrator ignores player input at T7. Weakest pipeline: Narrate (2) and Extract State (2).

### V2 — Narrative Quality → 3
Prose is strong and atmospheric. Mechanics drive fiction well. However, ignoring player input at T7 breaks agency and immersion.

### V3 — System Cohesion → 3
Pipelines mostly work together. Handoffs are clean except for state extraction failures on spending. Compaction sanitization logging is absent.

### V4 — Prompt Quality → 3
Narrate prompt fails on input priority. State prompt fails on spending rule. Redundancy in `present_npcs` blocks wastes tokens. Highest priority fix: Strengthen input priority rule in Narrate prompt.

### V5 — Compaction → 2
Chronicle bullets accurate. Sanitization fidelity rate 0.25 due to missing logging of `pressure_remove` and `condition_remove`.

### V6 — Pipeline I/O Relevance
Rules: Inputs focused. Outputs clean.
Narrate: Inputs rich, justified. Outputs clean.
Scene: Inputs focused. Outputs clean.
State: Inputs focused. Outputs fail on 0-stack spending.
Progress: Inputs complex but justified. Outputs clean.

### V7 — Key Findings
1. Narrator violates "Player input is truth" rule at T7, replacing player action with combat. Fix: Add explicit negative constraint to Narrate prompt.
2. State extractor fails spending rule at T6, T9, T13, emitting invalid deltas for 0-stack `credits`. Fix: Add rule to omit remove deltas when item not in inventory.
3. Compaction sanitization not logging applied actions. Fix: Ensure compactor outputs sanitization results to trace.
4. Highest priority fix: Strengthen Narrate prompt input priority rule and fix State prompt spending rule.

---

# SECTION 11 — Trace Quality and Eval Self-Assessment

### 11A — Input Sufficiency

| Data Category | Rating | Notes |
|---|---|---|
| System prompts (all 5 pipelines) | SUFFICIENT | Complete and correctly attributed. |
| Per-turn user prompts (all 5 pipelines) | SUFFICIENT | Fully visible. |
| Per-turn engine outputs (rules, narrate, extractors) | SUFFICIENT | Complete. |
| State snapshots (per turn) | SUFFICIENT | Full snapshots/diffs sufficient to verify drift. |
| Applied/rejected deltas | SUFFICIENT | Detailed enough to verify correctness. |
| Context telemetry (token counts, trim status) | SUFFICIENT | Sufficient to assess prompt bloat. |
| Static context (pack style, seed state, engine constants) | SUFFICIENT | Complete and accurate. |
| Compaction signals | SUFFICIENT | Compaction events correctly identified. |
| Auto-checker signals | SUFFICIENT | Failures clearly attributed. |

### 11B — Missing Data
- **Compaction sanitization logs** — Needed for: Evaluating compaction fidelity. Source: Compactor pipeline.
- **Exact token waste from redundancy** — Needed for: Prompt quality audit. Source: Harness telemetry.

### 11C — Questions You Could Not Answer
- **Exact token waste from redundancy** — Could not assess because: Telemetry only reports estimated counts, not per-block waste. What data would have enabled it: Per-prompt block tokenization breakdown.

### 11D — Trace Structure Suggestions
1. **Most useful section:** Deterministic Signals (Auto-Checker Failures). Authoritative and precise.
2. **Least useful section:** Prompt Redundancy preview. Hard to assess impact without exact token counts.
3. **One piece of data to add:** Per-prompt block token counts for redundancy analysis.
4. **Compaction signal reliability:** Reliable. No false compaction events detected.

---

# SECTION 12 — Actionable Issues

**Critical:**
- **Narrator ignores player input priority rule** (turns: 7) — Failure mode: bad prompt. Remediation: Add explicit negative constraint to Narrate system prompt: "NEVER replace player input with a different action. If input conflicts with beat, narrate input FIRST, then integrate beat."
- **State extractor fails spending rule on 0-stack items** (turns: 6, 9, 13) — Failure mode: bad prompt. Remediation: Add explicit rule to Extract State system prompt: "If narration describes spending an item not in inventory, emit NO `inventory_remove`. Do not invent phantom spends. Omit delta entirely."

**Major:**
- **Compaction sanitization not logging applied actions** (turns: 6, 12) — Failure mode: scope/domain mismatch. Remediation: Ensure compactor outputs sanitization results (`quest_close`, `pressure_remove`, `condition_remove`) to trace for observability.
- **`intent_verb` classification drift** (turns: 11) — Failure mode: scope/domain mismatch. Remediation: Add few-shot examples to Rules prompt for `intent_verb` selection when input contains multiple action types.

**Minor:**
- **`present_npcs` block duplicated across all prompts** (all turns) — Failure mode: wasted tokens. Remediation: Pass `present_npcs` as a compacted JSON array to Rules/Narrate instead of full text blocks.
- **Auto-checker false positives on location names** (turns: 2, 3, 4, 5, 7, 8, 9) — Failure mode: checker noise. Remediation: Update checker to exclude location names and common adverbs from NPC mention validation.

## Auto-Checker

**136 passed, 18 failed**

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
| 2 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Finally'] |
| 2 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 2 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 2 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 2 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 2 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 2 | `progress.quest_id_collision` | ❌ | quest_updates re-creates already-completed quest id='settle_the_debt' |
| 3 | `rules.rolled` | ✅ | rolled=True |
| 3 | `extract.progress.quest_updates` | ✅ | quest_updates[deliver_the_ledger] found |
| 3 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=3 |
| 3 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 3 | `universal.location_change.applied` | ✅ | (no change) |
| 3 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 3 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 3 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 3 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 3 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 3 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 3 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 4 | `rules.rolled` | ✅ | rolled=False |
| 4 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 4 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 4 | `universal.location_change.applied` | ✅ | marrows_crossing -> merchant_road_east |
| 4 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 4 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 4 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 4 | `universal.scene.npc_cap` | ✅ | 0 NPCs |
| 4 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 4 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 4 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 5 | `rules.rolled` | ✅ | rolled=True |
| 5 | `extract.scene.scene_tags` | ❌ | scene_tags[combat] not found |
| 5 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=5 |
| 5 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 5 | `universal.location_change.applied` | ✅ | (no change) |
| 5 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 5 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed', 'Crossing'] |
| 5 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 5 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 5 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 5 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 5 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 6 | `rules.rolled` | ✅ | rolled=True |
| 6 | `extract.state.inventory_remove` | ❌ | inventory_remove[credits] not found |
| 6 | `extract.progress.quest_updates` | ❌ | quest_updates[clear_the_road_toughs] not found |
| 6 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 6 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 6 | `universal.location_change.applied` | ✅ | (no change) |
| 6 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 6 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 6 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 6 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 6 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 6 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 6 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 7 | `extract.progress.quest_updates` | ❌ | quest_updates[deliver_the_ledger] not found |
| 7 | `extract.progress.quest_status` | ❌ | quest[deliver_the_ledger] not found in quest_updates |
| 7 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=7 |
| 7 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 7 | `universal.location_change.applied` | ✅ | (no change) |
| 7 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 7 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 7 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 7 | `universal.scene.npc_cap` | ✅ | 4 NPCs |
| 7 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 7 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 7 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 8 | `rules.rolled` | ✅ | rolled=True |
| 8 | `extract.state.inventory_remove` | ❌ | inventory_remove[brass_key] not found |
| 8 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=8 |
| 8 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 8 | `universal.location_change.applied` | ✅ | (no change) |
| 8 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 8 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 8 | `universal.recent_events.ring_bounded` | ✅ | 6 entries |
| 8 | `universal.scene.npc_cap` | ✅ | 4 NPCs |
| 8 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 8 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 8 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 9 | `rules.rolled` | ✅ | rolled=True |
| 9 | `extract.scene.scene_tags` | ❌ | scene_tags[social] not found |
| 9 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 9 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 9 | `universal.location_change.applied` | ✅ | (no change) |
| 9 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 9 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 9 | `universal.recent_events.ring_bounded` | ✅ | 6 entries |
| 9 | `universal.scene.npc_cap` | ✅ | 4 NPCs |
| 9 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 9 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 9 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 10 | `rules.rolled` | ✅ | rolled=True |
| 10 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=10 |
| 10 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 10 | `universal.location_change.applied` | ✅ | merchant_road_east -> crossed_keys_inn_interior |
| 10 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 10 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 10 | `universal.recent_events.ring_bounded` | ✅ | 7 entries |
| 10 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 10 | `universal.pc.condition_no_dupes` | ✅ | 3 conditions, no dupes |
| 10 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 10 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 11 | `rules.rolled` | ✅ | rolled=True |
| 11 | `extract.scene.scene_tags` | ✅ | scene_tags[combat] found |
| 11 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=11 |
| 11 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 11 | `universal.location_change.applied` | ✅ | (no change) |
| 11 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 11 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 11 | `universal.recent_events.ring_bounded` | ✅ | 8 entries |
| 11 | `universal.scene.npc_cap` | ✅ | 4 NPCs |
| 11 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 11 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 11 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 12 | `rules.rolled` | ❌ | rolled=True |
| 12 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=12 |
| 12 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 12 | `universal.location_change.applied` | ✅ | crossed_keys_inn_interior -> river_docks_alleyway |
| 12 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 12 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 12 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 12 | `universal.scene.npc_cap` | ✅ | 0 NPCs |
| 12 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 12 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 12 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 13 | `rules.rolled` | ✅ | rolled=False |
| 13 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 13 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 13 | `universal.location_change.applied` | ✅ | (no change) |
| 13 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 13 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 13 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 13 | `universal.scene.npc_cap` | ✅ | 0 NPCs |
| 13 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 13 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 13 | `universal.momentum.band_delta` | ✅ | (no roll) |

## Turn Metrics

| # | input | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | retries | parse_fail | duration_s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | Walk over to Caron's table and sit down across f… | 1403 (+0) | 3114 (+115) | 2448 (+9) | 3215 (+278) | 4393 (+182) | 0 | 0 | 35.69 |
| 2 | I slide 500 credits across the table to Caron an… | 1734 (+5) | 3312 (+132) | 2804 (+117) | 3259 (+348) | 4701 (+253) | 0 | 0 | 26.82 |
| 3 | I find Halden by the town well and offer to carr… | 1789 (+79) | 3676 (+194) | 2917 (+182) | 3303 (+364) | 4764 (+281) | 0 | 0 | 34.17 |
| 4 | I leave Marrow's Crossing by the east gate and h… | 1807 (+80) | 3961 (+290) | 2702 (-72) | 3198 (+141) | 4519 (+91) | 0 | 0 | 27.67 |
| 5 | I walk up to the two toughs at the inn door and … | 1633 (-224) | 3976 (-113) | 2596 (-286) | 3325 (+345) | 4532 (-162) | 0 | 0 | 33.05 |
| 6 | I drop 200 credits on the ground between the tou… | 1855 (+61) | 4227 (+51) | 2891 (+71) | 3272 (+278) | 4822 (+201) | 0 | 0 | 40.08 |
| 7 | I sit across from Halden at his table, slide the… | 1820 (+39) | 4312 (-8) | 2868 (+105) | 3276 (+335) | 4779 (+210) | 0 | 0 | 34.91 |
| 8 | I pull out the brass key Halden gave me and try … | 1827 (+85) | 4461 (+255) | 2891 (+154) | 3245 (+305) | 4851 (+330) | 0 | 0 | 33.07 |
| 9 | I press my ear against the inn's stone wall and … | 1791 (+69) | 4410 (+284) | 2783 (+58) | 3171 (+218) | 4813 (+284) | 0 | 0 | 29.08 |
| 10 | I approach Matthew Estrada at the bar, grab his … | 1755 (+1) | 4292 (+232) | 2835 (-5) | 3261 (+225) | 4867 (+178) | 0 | 0 | 37.82 |
| 11 | Matthew's bodyguard draws a knife! I tackle him … | 1783 (-20) | 4266 (+118) | 2833 (+38) | 3285 (+323) | 4885 (+251) | 0 | 0 | 35.61 |
| 12 | I grab the ledger from my coat and sprint out th… | 1797 (+13) | 4360 (+61) | 2903 (+59) | 3279 (+339) | 4958 (+229) | 0 | 0 | 49.27 |
| 13 | I find a quiet corner at the dock and wrap my wo… | 1691 (+19) | 4352 (-42) | 2654 (+50) | 3310 (+333) | 4614 (+198) | 0 | 0 | 31.31 |
|  | TOTALS | 22685 | 52719 | 36125 | 42399 | 61498 | 0 | 0 | 448.56 |

**Total turns:** 13 · **Total duration:** 448.56s · **Avg/turn:** 34.50s
**Total tokens in:** 215,426 · **Total tokens out:** 177,461 · **Total LLM time:** 422.4s
**Total retries:** 0 · **Total parse failures:** 0


## Warnings (≥ warn threshold but < fail threshold)

- `extraction.state` turn 2: 2911 → 3259 (+12.0%)
- `extraction.state` turn 3: 2939 → 3303 (+12.4%)
- `extraction.state` turn 5: 2980 → 3325 (+11.6%)
- `extraction.state` turn 7: 2941 → 3276 (+11.4%)
- `extraction.state` turn 8: 2940 → 3245 (+10.4%)
- `extraction.state` turn 11: 2962 → 3285 (+10.9%)
- `extraction.state` turn 12: 2940 → 3279 (+11.5%)
- `extraction.state` turn 13: 2977 → 3310 (+11.2%)
