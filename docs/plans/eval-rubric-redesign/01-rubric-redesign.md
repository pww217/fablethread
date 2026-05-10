# Eval Rubric Redesign — Verdict Expansion, Storytelling Trace, Cross-Pipeline Correlation

**Eval run reference:** `evals/runs/20260510T180913Z_2do6ma7m` · `full_cycle` (13 turns)  
**Current rubric:** `evals/rubrics/default.md` (646 lines)  
**Related:** `eval-remediation-may10/02-extraction-quality.md` (extraction-quality criteria added in Phase 6)

---

## Problem Statement

The current rubric has four structural gaps:

1. **The Verdict is too thin.** It's a single 2-4 sentence paragraph that doesn't reflect the depth of analysis happening in the detailed sections below. The judge produces rich per-pipeline scores, 12 storytelling criteria, and extraction-quality assessments — but the Verdict doesn't summarize or group these into digestible categories.

2. **The rubric lacks trace sections.** The judge reads about momentum, beats, and pressure as abstract criteria but never sees a representative trace showing how these mechanics actually played out turn-by-turn. There's no "Storytelling Trace" or "State Evolution Trace" section.

3. **The rubric evaluates pipelines in isolation.** There's no section checking if mechanics from different pipelines interact correctly (e.g., rules failure → condition extracted → narrator honors it → pressure escalates).

4. **Missing criteria:** NPC voice (distinct behaviors), world reactivity (world responds to player actions), failure arc (what happens when the player fails repeatedly), and scenario quality (does the scenario exercise all mechanics?).

5. **The Verdict is at the top.** The judge is asked to synthesize a conclusion before it has done the analysis. LLMs reason better when they produce evidence first, then conclusion.

6. **Redundant criteria.** `directive_narration_binding` and `stakes_routing` are fully covered by the new Cross-Pipeline Correlation section. `momentum_arc`, `pressure_arc`, `beat_lifecycle`, `consequence_persistence`, and `rewards_and_consequences` currently ask the judge to collect data (plot momentum, plot pressure, check beat lifecycle) that the new trace sections will collect once.

7. **Output Format section is redundant.** Lines 526-645 show a verbose template of what the judge should output. The judge already knows the format from the section descriptions above.

---

## Proposed New Rubric Structure

### Before (current)

```
1. Verdict (2-4 sentences)
2. Actionable Issues Surfaced
3. Mechanical Design Critique (per-pipeline)
4. Storytelling Design Critique (12 criteria)
5. Prompt Redundancy Analysis
6. Compaction Capabilities Report
7. Auto-Checker Failures
8. Additional Observations
```

### After (proposed)

```
1. Storytelling Trace (new — short, data collection)
2. State Evolution Trace (new — short, data collection)
3. Mechanical Design Critique (per-pipeline, unchanged)
4. Cross-Pipeline Correlation (new — interaction analysis)
5. Storytelling Design Critique (11 criteria: 7 kept + 4 new, 5 simplified)
6. Prompt Redundancy Analysis (unchanged)
7. Compaction Capabilities Report (unchanged)
8. Auto-Checker Failures (unchanged)
9. Verdict (expanded with subheaders, at the end)
10. Additional Observations (unchanged)
```

### Storytelling Design Critique — criteria changes

| Criterion | Action |
|---|---|
| `quest_arc_quality` | Keep as-is |
| `rewards_and_consequences` | Simplify — remove per-roll data collection, reference traces |
| `narrative_compellingness` | Keep as-is |
| `npc_development` | Keep as-is |
| `npc_voice` | **New** — distinct NPC voices/behaviors |
| `world_consistency` | Keep as-is |
| `world_reactivity` | **New** — world responds to player actions |
| `player_agency` | Keep as-is |
| `failure_arc` | **New** — failures create interesting options |
| `pacing_and_pressure` | Keep as-is |
| `deescalation_mechanics` | Keep as-is |
| ~~`momentum_arc`~~ | **Removed** — data collected in Momentum Trace |
| ~~`pressure_arc`~~ | **Removed** — data collected in Scene Pressure Trace |
| ~~`beat_lifecycle`~~ | **Removed** — data collected in GM Beat Trace |
| ~~`consequence_persistence`~~ | **Removed** — data collected in Condition/Pressure Traces |
| ~~`directive_narration_binding`~~ | **Removed** — covered by Cross-Pipeline Correlation |
| ~~`stakes_routing`~~ | **Removed** — covered by Cross-Pipeline Correlation |
| `scenario_quality` | **New** — does scenario exercise all mechanics |

Net: 14 → 11 criteria. Saves ~80 lines of rubric text while adding ~100 lines of trace sections.

---

## Phase 1: Add Storytelling Trace Section

**File:** `evals/rubrics/default.md`  
**Type:** New rubric section  
**Risk:** Low — adds a new section for the judge to produce

### Problem

The rubric has criteria but no representative trace showing mechanics in action. The judge reads about momentum, beats, and pressure as abstract criteria but never sees a concrete turn-by-turn trace of how they actually played out.

### Fix

Add a new section at the top (after the front matter and Table of Contents, before Actionable Issues Surfaced) that asks the judge to produce short, concise representative traces of each narrative mechanic. Traces are data collection — keep them brief.

```markdown
## Section 1: Storytelling Trace

Produce a short trace for each narrative mechanic. Cite specific turns and state values. Keep each trace to 3-5 lines — this is data collection, not analysis.

### Momentum Trace
List each turn where `pc.momentum` changed: `T<n>: band=<band> <before>→<after>`. Note if narration tone matched momentum. Flag wrong-direction or flat momentum on significant rolls.

### GM Beat Trace
List each GM beat: `T<n>: generated=<instruction> → T<m>: surfaced=<yes/no> → impact=<none/complication/revelation/opportunity/breathing>`. Flag beats generated but never surfaced, or surfaced with no effect.

### Scene Pressure Trace
List each pressure: `T<n>: added=<description> urgency=<level> → escalated=<yes/no> → resolved=<yes/no>`. Flag pressures that sat inert across multiple turns. Flag `urgency: immediate` pressures without higher-stakes narration.

### Condition Lifecycle Trace
List each condition: `T<n>: added=<condition> → T<m>: still_present=<yes/no> → resolved=<yes/no, justification>`. Flag conditions that appeared and silently disappeared.

### Quest Arc Trace
List each quest: `T<n>: created=<quest_id> → T<m>: objectives_done=<list> → resolved=<completed/failed/abandoned>`. Flag quests created but never advanced, or completed without all objectives done.

### Inventory Evolution Trace
List each significant inventory change: `T<n>: <add/remove> <item> qty=<n>`. Note if narration reflected the change. Flag narration describing spending/gaining items with no corresponding extract.
```

### Verification

- Read the updated rubric and verify the trace sections are short (3-5 lines each) and actionable
- Verify the trace sections reference data available in the trace (state snapshots, extract outputs)
- Verify the trace sections don't require information not present in the trace

---

## Phase 2: Add State Evolution Trace Section

**File:** `evals/rubrics/default.md`  
**Type:** New rubric section  
**Risk:** Low — adds a new section for the judge to produce

### Problem

The rubric has no section showing how the game state evolves across turns. The judge evaluates individual mechanics but doesn't assess whether the overall state evolution is logical and coherent.

### Fix

Add a new section after the Storytelling Trace that asks the judge to assess state evolution. Keep this section short — it's a higher-level check, not a detailed analysis.

```markdown
## Section 2: State Evolution Trace

Assess how the game state evolved across the run. Keep this to 5-10 lines total — high-level coherence check, not a detailed analysis.

### State Coherence
Does the game state evolve logically? Note: inventory matches gains/losses, conditions persist until resolved, quests advance toward completion, pressures escalate or resolve. Flag any state entries inconsistent with narration or prior turns.

### State Drift
Are there any state entries that drift from expected values? Note: inventory items in narration but not state, conditions removed but narration still references them, quests completed but state still active. Flag drift and note whether it's a state extraction issue or narration issue.

### State Completeness
Are there any state domains that should have changed but didn't? Note: location changes not reflected in `state.location.id`, NPC interactions not reflected in `state.scene.present_npcs`, quest completions not reflected in `state.quests`. Flag missing updates and note which pipeline failed.
```

### Verification

- Read the updated rubric and verify the state evolution sections are short (5-10 lines total) and actionable
- Verify the state evolution sections reference data available in the trace (state snapshots)
- Verify the state evolution sections don't require information not present in the trace

---

## Phase 3: Add Cross-Pipeline Correlation Section

**File:** `evals/rubrics/default.md`  
**Type:** New rubric section  
**Risk:** Low — adds a new section for the judge to produce

### Problem

The rubric evaluates each pipeline in isolation. There's no section checking if mechanics from different pipelines interact correctly (e.g., rules failure → condition extracted → narrator honors it → pressure escalates).

### Fix

Add a new section after Mechanical Design Critique (before Storytelling Design Critique) that asks the judge to assess cross-pipeline correlation. This is analysis, not data collection — it can be as long as needed.

```markdown
## Section 4: Cross-Pipeline Correlation

Assess how well the engine's pipelines work together. The rubric's per-pipeline analysis (Section 3) evaluates each pipeline in isolation; this section evaluates the interactions between pipelines.

### Rules → Narrate Binding
For each turn with a dice roll, verify the full chain: rules outcome → narrator binding → narration outcome. Flag turns where:
- The roll band was `fail`/`setback` but the narration described a success
- The roll band was `crit_success` but the narration described a failure
- The roll directive was not honored by the narration

### Rules → State Extract Routing
For each turn with a dice roll, verify that stakes routing produced observable mechanical consequences:
- When `stakes` named a condition and `band` was `setback`/`fail`/`crit_fail`, was the condition extracted by state extractor?
- When `stakes` named a consequence and `band` was `crit_fail`, was a `scene_pressure_add` emitted by progress extractor?
- When `stakes` named a consequence and `band` was `crit_success`, was an `opportunity` or `escalation` beat considered?
Flag turns where stakes were named but no mechanical consequence followed.

### Narrate → Scene Extract Consistency
For each turn where the narrator described an NPC interaction, location change, or scene shift, verify that the scene extractor captured it:
- Narration mentions a new NPC → scene extract has `npc_add` or `npc_update`
- Narration describes a location change → scene extract has `location_change`
- Narration describes a scene shift → scene extract has `scene_tags` or `scene_tagline`
Flag turns where narration described changes that the scene extractor missed.

### Narrate → State Extract Consistency
For each turn where the narrator described an inventory change or condition change, verify that the state extractor captured it:
- Narration describes gaining an item → state extract has `inventory_add`
- Narration describes spending/losing an item → state extract has `inventory_remove`
- Narration describes a condition being gained or resolved → state extract has `pc_condition_add` or `pc_condition_remove`
Flag turns where narration described changes that the state extractor missed.

### Narrate → Progress Extract Consistency
For each turn where the narrator described a quest update, recent event, or pressure change, verify that the progress extractor captured it:
- Narration describes a quest objective completion → progress extract has `quest_updates`
- Narration describes a new significant fact → progress extract has `recent_events_add`
- Narration describes a pressure being added or resolved → progress extract has `scene_pressure_add` or `scene_pressure_remove`
Flag turns where narration described changes that the progress extractor missed.

### State → Progress Extract Handoff
Verify that the state → progress extract handoff works correctly:
- `items_gained` (item names from `inventory_add`) appears in progress extract context
- `items_lost` (item IDs from `inventory_remove`) appears in progress extract context
- Progress extract uses this information when generating `actions` or `outcome_summary`
Flag turns where the handoff appears broken (e.g., progress extract mentions items not in `items_gained`/`items_lost`).

### Progress → Narrate Feedback Loop
Verify that the progress → narrate feedback loop works correctly:
- `gm_beat` generated in turn N is surfaced in narration of turn N+1
- `recent_events_add` from turn N appears in `recent_turns` context of turn N+1
- `scene_pressure_add` from turn N appears in rules context of turn N+1
Flag turns where the feedback loop appears broken.
```

### Verification

- Read the updated rubric and verify the cross-pipeline correlation sections are clear and actionable
- Verify the cross-pipeline correlation sections reference data available in the trace
- Verify the cross-pipeline correlation sections don't require information not present in the trace

---

## Phase 4: Update Storytelling Design Critique Criteria

**File:** `evals/rubrics/default.md`  
**Type:** Rubric criteria changes  
**Risk:** Low — removes 5 criteria, adds 4 new, simplifies 5

### Problem

The rubric has redundant criteria (`directive_narration_binding`, `stakes_routing` covered by Cross-Pipeline Correlation) and criteria that duplicate data collection now handled by trace sections (`momentum_arc`, `pressure_arc`, `beat_lifecycle`, `consequence_persistence`, `rewards_and_consequences`). It's also missing criteria for NPC voice, world reactivity, failure arc, and scenario quality.

### Fix

Replace the entire Storytelling Design Critique section (Section 4 in current rubric, which will become Section 5 after the new sections are inserted) with the updated version below.

**Removed criteria:** `momentum_arc`, `pressure_arc`, `beat_lifecycle`, `consequence_persistence`, `directive_narration_binding`, `stakes_routing` (6 removed)

**Simplified criteria:** `rewards_and_consequences` (removed per-roll data collection, now references traces)

**New criteria:** `npc_voice`, `world_reactivity`, `failure_arc`, `scenario_quality` (4 added)

**Net: 14 → 11 criteria**

```markdown
## Section 5: Storytelling Design Critique (SECONDARY)

The narrative quality serves as a check on whether the mechanics are producing good fiction. A 5/5 story built on broken extraction is a false positive.

For each of the narrative criteria below, score 1-5 with two or more sentences and citations to specific turns. Criteria marked [trace] reference data collected in the Storytelling Trace section above — do not re-collect data, just evaluate the quality of what the trace shows.

### quest_arc_quality
Did quests form a compelling long arc? Did completing or failing them feel earned and create interesting consequences?

### rewards_and_consequences [trace]
Did the game give real rewards for success and real consequences for failure? Score based on the overall pattern shown in the Momentum Trace, GM Beat Trace, and Condition Lifecycle Trace — did successful rolls produce positive momentum and conditions, did failures produce negative momentum and costs, did beats create meaningful story moments? Do not re-check individual rolls; the traces above already show the data.

### narrative_compellingness
Was the overall story compelling enough to keep playing? Did choices matter?

### npc_development
Did NPCs evolve and react meaningfully across turns?

### npc_voice
Do NPCs have distinct voices and behaviors, or do they feel interchangeable? Score this criterion by checking:
- **Distinct speech patterns:** Do different NPCs use different language, tone, or phrasing? Flag turns where multiple NPCs speak with identical or near-identical dialogue.
- **Distinct behaviors:** Do different NPCs react differently to the same situation? Flag turns where multiple NPCs react identically to the same player action.
- **Consistent characterization:** Do NPCs maintain their established personality across turns? Flag turns where an NPC's behavior contradicts their established characterization.
Score based on the proportion of NPC interactions where distinct voice/behavior is maintained. A run where all NPCs sound the same scores 1-2.

### world_consistency
Were all entities (NPCs, locations, items) that appeared in narration sanctioned by the engine, worldpack, or player input? Flag any unsanctioned introductions — invented NPCs, unregistered locations, items with no extraction grounding. This is a trust axis distinct from how existing NPCs are developed.

### world_reactivity
Does the world react to the player's actions, or does it feel static? Score this criterion by checking:
- **Faction shifts:** Do factions change their disposition toward the player based on player actions? Flag turns where the player takes significant actions but no faction response follows.
- **Location changes:** Do locations change based on player actions or time passage? Flag turns where locations remain static despite significant player activity.
- **NPC memory:** Do NPCs reference past events or player actions from previous turns? Flag turns where NPCs act as if they have no memory of prior interactions.
- **Consequence propagation:** Do player actions create ripple effects across the world? Flag turns where significant player actions have no observable effect beyond the immediate scene.
Score based on the proportion of turns where the world shows observable reactivity to player actions. A run where the world feels static scores 1-2.

### player_agency
Did the game respect player choice? Did failures create new options rather than dead-ends? Did the engine honor the player's stated action rather than redirecting or reinterpreting it?

### failure_arc [trace]
When the player fails, does the game create interesting new options or dead ends? Score based on the Condition Lifecycle Trace and Momentum Trace — did failures produce lasting conditions that affected future turns, did negative momentum create interesting narrative tension, did different failure types (crit_fail, fail, setback, partial) produce different outcomes? Flag failures that were immediately forgotten or produced no downstream effect.

### pacing_and_pressure
Score based on narrative pacing: breathing room between high-tension turns, momentum tone alignment (does narration at +2+ feel like a strong run? does narration at −2− offer relief unless fiction demands otherwise?), and overall arc satisfaction. The mechanical pressure component is evaluated separately under the Scene Pressure Trace.

### deescalation_mechanics
Did deescalation work as a pressure-resolution mechanic?

**Mechanical checks:**
- When `deescalate > 0` (success/crit_success on active pressure), did the narration avoid adding new pressures?
- When `deescalate >= 0.8` (success on immediate pressure), was a `breathing_room` beat type preferred or no beat emitted?
- When `deescalate >= 1.0` (crit_success on immediate pressure), were new pressures suppressed entirely?
- Flag turns where deescalation was active but new pressures were added.

Score based on the proportion of deescalation turns where the mechanic was respected.

### scenario_quality
Does the scenario exercise the engine's mechanics adequately? Score this criterion by checking:
- **Mechanic coverage:** Does the scenario include turns that exercise all major mechanics (dice rolls, inventory changes, condition changes, quest progression, pressure escalation, GM beats, location changes)? Flag mechanics that are never exercised.
- **Turn variety:** Does the scenario include a variety of turn types (combat, social, exploration, investigation, travel, rest)? Flag scenarios where all turns are the same type.
- **Pacing:** Does the scenario have a good mix of high-tension and low-tension turns? Flag scenarios where all turns are equally tense or equally calm.
- **Narrative arc:** Does the scenario have a clear narrative arc (setup, development, climax, resolution)? Flag scenarios where the narrative feels aimless or repetitive.
Score based on the proportion of mechanics exercised and the variety of turn types. A scenario that only exercises 2-3 mechanics scores 1-2.
```

### Verification

- Read the updated rubric and verify the new criteria are clear and actionable
- Verify the removed criteria are fully covered by other sections
- Verify the simplified criteria reference the trace sections and don't duplicate data collection
- Verify the new criteria reference specific failure modes that can be observed in the trace

---

## Phase 5: Move and Expand the Verdict

**File:** `evals/rubrics/default.md`  
**Type:** Rubric instruction change  
**Risk:** Low — changes judge output format, not engine logic

### Problem

The Verdict is a single 2-4 sentence paragraph at the top of the rubric. The judge is asked to synthesize a conclusion before it has done the analysis. LLMs reason better when they produce evidence first, then conclusion. The Verdict also lacks subheaders to group related findings.

### Fix

Move the Verdict to the end of the rubric (after Auto-Checker Failures, before Additional Observations). Expand it with subheaders that group related fields analyzed in the detailed sections. The verdict can be as long as needed for insightful end-to-end analysis.

Replace the current Verdict section (Section 1, lines 92-99) with a placeholder that will be moved:

```markdown
## Section 8: Verdict

### Mechanical Integrity
Summarize the mechanical health of the run. Reference pipeline scores (rules, narrate, extract_scene, extract_state, extract_progress) and note which pipelines had major failures. Mention extraction quality issues (amount accuracy, spending action extraction, quest dedup, ambient NPC filtering). Score: 1-5.

### Narrative Quality
Summarize the narrative health of the run. Reference storytelling criteria scores (quest_arc_quality, rewards_and_consequences, narrative_compellingness, npc_development, npc_voice, world_consistency, world_reactivity, player_agency, failure_arc, pacing_and_pressure, deescalation_mechanics, scenario_quality). Note which criteria scored lowest. Score: 1-5.

### System Cohesion
Summarize how well the engine's systems work together. Reference cross-pipeline correlation findings (do mechanics from different pipelines interact correctly?), state evolution trace (does the game state evolve logically?), and scenario quality (does the scenario exercise all mechanics?). Score: 1-5.

### Regression & Known Issues
Note any regressions from previous eval runs (criteria that scored lower than before, new auto-checker failures, new extraction quality issues). Note any known issues that were confirmed again this run. Flag any issues that were previously reported but not fixed.

### Key Findings
2-4 sentences. Concrete, specific, actionable. Reference turn numbers. Justify why mechanical_score diverges from narrative_score if applicable. End with the single most important fix the engine needs.
```

### Verification

- Read the updated rubric and verify the Verdict structure is clear and actionable
- Verify the subheaders map to sections that exist in the rubric
- Verify the scoring guidance is consistent with the detailed sections
- Verify the Verdict is positioned at the end, after all analysis sections

---

## Phase 6: Update Table of Contents and Remove Output Format

**File:** `evals/rubrics/default.md`  
**Type:** Rubric structure update  
**Risk:** Low — updates TOC and removes redundant section

### Problem

The Table of Contents needs to reflect the new rubric structure. The Output Format section (lines 526-645) is redundant — the judge already knows the format from the section descriptions.

### Fix

Replace the Table of Contents (lines 11-19) with the updated version. Use hyphens for spaces in link anchors (e.g., `#compaction-capabilities-report`), matching the existing format in the rubric.

```markdown
# Table of Contents
- [Storytelling Trace](#storytelling-trace)
  - [Momentum Trace](#momentum-trace)
  - [GM Beat Trace](#gm-beat-trace)
  - [Scene Pressure Trace](#scene-pressure-trace)
  - [Condition Lifecycle Trace](#condition-lifecycle-trace)
  - [Quest Arc Trace](#quest-arc-trace)
  - [Inventory Evolution Trace](#inventory-evolution-trace)
- [State Evolution Trace](#state-evolution-trace)
  - [State Coherence](#state-coherence)
  - [State Drift](#state-drift)
  - [State Completeness](#state-completeness)
- [Mechanical Design Critique](#mechanical-design-critique)
- [Cross-Pipeline Correlation](#cross-pipeline-correlation)
- [Storytelling Design Critique](#storytelling-design-critique)
- [Prompt Redundancy Analysis](#prompt-redundancy-analysis)
- [Compaction Capabilities Report](#compaction-capabilities-report)
- [Auto-Checker Failures](#auto-checker-failures)
- [Verdict](#verdict)
  - [Mechanical Integrity](#mechanical-integrity)
  - [Narrative Quality](#narrative-quality)
  - [System Cohesion](#system-cohesion)
  - [Regression & Known Issues](#regression--known-issues)
  - [Key Findings](#key-findings)
- [Actionable Issues Surfaced](#actionable-issues-surfaced)
- [Additional Observations](#additional-observations)
```

Delete the Output Format section entirely (lines 526-645). The judge produces the markdown body based on the section instructions — it doesn't need a template showing exactly what the output should look like.

### Verification

- Read the updated rubric and verify the Table of Contents matches the new structure
- Verify the Output Format section is fully removed
- Verify the remaining section numbers are consistent (the judge doesn't reference section numbers in its output, but the TOC should be accurate)

---

## Phase 7: Update REPOMAP and TODO

**Files:** `docs/REPOMAP/eval.md`, `docs/plans/TODO.md`  
**Type:** Documentation update  
**Risk:** Low — updates documentation only

### Fix

Update `docs/REPOMAP/eval.md` to note the rubric redesign:

```markdown
- `evals/rubrics/default.md` — Judge rubric with Storytelling Trace section (momentum, GM beat, scene pressure, condition lifecycle, quest arc, inventory evolution), State Evolution Trace section (coherence, drift, completeness), Cross-Pipeline Correlation section (rules→narrate, rules→state, narrate→scene, narrate→state, narrate→progress, state→progress, progress→narrate), Storytelling Design Critique with 11 criteria (quest_arc_quality, rewards_and_consequences [trace], narrative_compellingness, npc_development, npc_voice, world_consistency, world_reactivity, player_agency, failure_arc [trace], pacing_and_pressure, deescalation_mechanics, scenario_quality), Verdict at end with subheaders (Mechanical Integrity, Narrative Quality, System Cohesion, Regression & Known Issues, Key Findings)
```

Update `docs/plans/TODO.md` to add new items:

```markdown
- [ ] **Rubric redesign: storytelling trace** — add Storytelling Trace section (momentum, GM beat, scene pressure, condition lifecycle, quest arc, inventory evolution) — see `[eval-rubric-redesign/01-rubric-redesign.md](eval-rubric-redesign/01-rubric-redesign.md) Phase 1`
- [ ] **Rubric redesign: state evolution trace** — add State Evolution Trace section (coherence, drift, completeness) — see `[eval-rubric-redesign/01-rubric-redesign.md](eval-rubric-redesign/01-rubric-redesign.md) Phase 2`
- [ ] **Rubric redesign: cross-pipeline correlation** — add Cross-Pipeline Correlation section (rules→narrate, rules→state, narrate→scene, narrate→state, narrate→progress, state→progress, progress→narrate) — see `[eval-rubric-redesign/01-rubric-redesign.md](eval-rubric-redesign/01-rubric-redesign.md) Phase 3`
- [ ] **Rubric redesign: storytelling criteria** — remove 6 criteria, add 4 new, simplify 5 to reference traces — see `[eval-rubric-redesign/01-rubric-redesign.md](eval-rubric-redesign/01-rubric-redesign.md) Phase 4`
- [ ] **Rubric redesign: verdict** — move verdict to end, expand with subheaders (Mechanical Integrity, Narrative Quality, System Cohesion, Regression & Known Issues, Key Findings) — see `[eval-rubric-redesign/01-rubric-redesign.md](eval-rubric-redesign/01-rubric-redesign.md) Phase 5`
- [ ] **Rubric redesign: TOC and output format** — update Table of Contents, remove redundant Output Format section — see `[eval-rubric-redesign/01-rubric-redesign.md](eval-rubric-redesign/01-rubric-redesign.md) Phase 6`
```

---

## Ambiguities Resolved

1. **Storytelling Trace vs State Evolution Trace overlap:** Both sections ask the judge to produce traces. The Storytelling Trace focuses on narrative mechanics (momentum, beats, pressure) while the State Evolution Trace focuses on mechanical state coherence. The overlap is intentional — the Storytelling Trace shows how mechanics played out narratively, while the State Evolution Trace shows whether the state evolved logically. **RESOLVED: confirmed, traces are allowed to overlap somewhat.**

2. **Cross-Pipeline Correlation scope:** The proposed section has 7 subsections. This is a lot of analysis for the judge to produce. Alternative: reduce to 3-4 key subsections (Rules→Narrate, Narrate→Extractors, Progress→Narrate). Recommendation: keep all 7 — the rubric already has 12 storytelling criteria, so 7 cross-pipeline subsections is reasonable. **RESOLVED: keep all 7.**

3. **Scenario Quality placement:** The proposed placement is in Storytelling Design Critique. Alternative: place in Mechanical Design Critique (since it's about the eval scenario, not the game). Recommendation: keep in Storytelling Design Critique — it's about the quality of the narrative experience, not the mechanical design. **RESOLVED: keep in Storytelling Design Critique.**

4. **Verdict position:** LLMs reason better when they produce evidence first, then conclusion. Verdict should be at the end, not the beginning. **RESOLVED: verdict moves to end.**

5. **Trace length:** Traces are data collection — keep them short (3-5 lines each). Verdicts and detailed evaluations can be as long as needed for insightful end-to-end analysis. **RESOLVED: traces short, verdict/analysis long.**

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|---|---|---|
| Judge model can't handle the expanded rubric | Medium | The judge already produces 12 storytelling criteria; adding 4 more and 2 trace sections is within its capacity |
| Rubric becomes too long for judge context | Low | The rubric is ~650 lines; removing ~120 lines (Output Format + 6 criteria) and adding ~100 lines brings it to ~630 lines — actually shorter than current |
| Judge produces inconsistent traces | Medium | The trace sections have clear instructions and reference specific data points in the trace |
| Rubric redesign breaks existing eval runs | Low | The rubric is only used by the judge; existing eval runs are stored as REPORT.md files |
| Judge can't follow "reference trace, don't re-collect" instruction | Medium | The `[trace]` marker on simplified criteria makes this explicit |

---

## Execution Order

1. **Phase 1:** Add Storytelling Trace section (short, data collection)
2. **Phase 2:** Add State Evolution Trace section (short, data collection)
3. **Phase 3:** Add Cross-Pipeline Correlation section (analysis, can be long)
4. **Phase 4:** Update Storytelling Design Critique criteria (remove 6, add 4, simplify 5)
5. **Phase 5:** Move and expand Verdict to end with subheaders
6. **Phase 6:** Update Table of Contents, remove Output Format section
7. **Phase 7:** Update REPOMAP and TODO

All phases modify `evals/rubrics/default.md` only (except Phase 7 which also updates REPOMAP and TODO). No engine code changes required.
