# Eval Rubric & Architecture Update Plan

## Objective

Update `evals/rubrics/default.md` and `docs/ARCHITECTURE.md` to:

1. **Fix ARCHITECTURE.md inaccuracies** — Scene Extract no longer owns `scene_pressure_add/remove/update` or `gm_beat`; Progress Extract does. The architecture doc still reflects pre-overhaul state.
2. **Expand the rubric** to judge ALL narrative mechanics end-to-end: momentum lifecycle, scene pressure lifecycle (add/update/remove/escalate/expiry/purge), GM beat lifecycle (generation/carry/consume/replace/TTL/consumption), directive binding (rules → narration), stakes/band routing to extractors, and deescalation mechanics.
3. **Reorganize report layout** — move Verdict and Actionable Issues to the top, keep detailed sections below.

---

## Part 1: ARCHITECTURE.md Fixes

### 1.1 Step 0 — Rules / Intent table (line 20)

**Current:** `state.scene.present_npcs` listed as input. `scene_pressure` listed as mechanic owned.

**Fix:** Remove `scene_pressure` from the "Mechanics it owns" column. Rules does NOT own scene pressure — it only reads it as context for difficulty. Add `scene_pressure` to the "Key inputs" column since it's fed to the rules LLM for context.

### 1.2 Step 2a — Scene Extract table (line 22)

**Current outputs listed:**
```
scene_tags, scene_tagline, location_change, npc_add/remove/update, compendium_npc_update,
scene_pressure_add/remove/update, gm_beat
```

**Actual outputs (post-overhaul):**
```
scene_tags, scene_tagline, location_change, location_description,
npc_add/remove/update, compendium_npc_update
```

**Fix:** Remove `scene_pressure_add/remove/update` and `gm_beat` from the outputs. Add `location_description` (it's missing from the table). Update the "Mechanics it owns" column to: "NPC presence, location changes, scene tags, scene classification (tags/tagline), durable NPC compendium identity."

**Fix the "Key inputs" column:** Remove `scene_pressure`, `deescalate`, `quest_ages` (these were removed by scene-progress-fixes.md). Keep: `narrative`, `state.pc/location`, `state.scene.present_npcs`, `state.pc.conditions`, `known_characters`, `RulesOutcome`, `recent_turns[-1:]`.

### 1.3 Step 2a — Scene Extract diagram (lines 163-208)

**Inputs to remove from diagram:** S9 (`scene_pressure`), S10 (`deescalate`), S11 (`quest_ages`).

**Outputs to remove from diagram:** O7 (`scene_pressure_add / remove / update`), O8 (`gm_beat`).

**Outputs to add:** O_new (`location_description: str | None`).

### 1.4 Step 2b — State Extract diagram (lines 215-247)

**Inputs to add:** `stakes` and `band` from rules_outcome (added by narrative-mechanics-overhaul.md Phase 3).

**Fix:** Add S10 (`stakes: str` from rules engine) and S11 (`band: str` from dice resolution) to inputs.

### 1.5 Step 2c — Progress Extract table (line 24)

**Current outputs listed:**
```
quest_updates, recent_events_add/update/remove, actions, outcome_summary
```

**Actual outputs (post-overhaul):**
```
quest_updates, recent_events_add/update/remove, actions, outcome_summary,
gm_beat, beat_disposition, scene_pressure_add/remove/update
```

**Fix:** Add `gm_beat`, `beat_disposition`, `scene_pressure_add`, `scene_pressure_remove`, `scene_pressure_update` to outputs. Update "Mechanics it owns" to: "Quest objectives, recent_events ring buffer, action suggestions, narrative recap, GM beat generation + disposition, scene pressure lifecycle (all three operations)."

**Current inputs listed:**
```
narrative, state.pc, state.scene.recent_events, state.scene.world_state,
active_quests, RulesOutcome, intent, recent_turns[-2:], items_gained/lost
```

**Actual inputs (post-overhaul):**
```
narrative, state.pc, state.scene.recent_events, state.scene.world_state,
active_quests, scene_pressure, RulesOutcome, intent, recent_turns[-2:],
items_gained/lost, stakes, band, deescalate, quest_ages, pending_beat
```

**Fix:** Add `scene_pressure`, `stakes`, `band`, `deescalate`, `quest_ages`, `pending_beat` to inputs.

### 1.6 Step 2c — Progress Extract diagram (lines 263-297)

**Outputs to add:**
- O7: `gm_beat: GMBeat | None` + O8: `beat_disposition: consume|carry|replace`
- O9: `scene_pressure_add: list[ScenePressure]`
- O10: `scene_pressure_remove: list[str]`
- O11: `scene_pressure_update: list[ScenePressure]`

**Inputs to add:**
- S11: `scene_pressure: list[ScenePressure]` (current pressures)
- S12: `stakes: str` (mechanical cost from rules)
- S13: `band: str` (dice resolution band)
- S14: `deescalate: float` (pressure resolution magnitude)
- S15: `quest_ages: list[dict]` (stalled-quest signal)
- S16: `pending_beat: dict | None` (carried beat from previous turn)

### 1.7 Step 2c — "Always runs" note (line 303)

**Current text:** "Scene-side forward signals (scene_pressure_*, pending_gm_beat) are sourced from the scene stream, not progress."

**Fix:** This is completely wrong post-overhaul. Replace with: "Progress is the post-narration storytelling brain. It always executes every turn (never skipped) and feeds next turn's rules call via recent_events_add (durable narrative facts), quest_updates (advancing or closing arcs), scene_pressure_add (new threats), and gm_beat (forward-facing beats stored in state.meta.pending_gm_beat)."

### 1.8 Delta Merge diagram (lines 311-338)

**StateDelta listing (line 323):** Currently shows `scene_pressure_add / remove / update` but doesn't show `gm_beat` or `beat_disposition` (correctly noted as not in StateDelta).

**Fix:** No change needed — the diagram correctly shows pressure fields in StateDelta and notes gm_beat is written directly to meta. This is accurate.

### 1.9 Cross-Pipeline Data Flow diagram (lines 377-404)

**Fix:** Update the arrow from STEP2A to show it no longer outputs scene_pressure or gm_beat. The arrow from STEP2C should show it outputs scene_pressure_add, gm_beat, and beat_disposition.

### 1.10 High-Level Overview mermaid (lines 32-66)

**Fix:** No structural change needed — the diagram is at a high level and doesn't show individual fields.

---

## Part 2: Rubric Updates

### 2.1 Restructure: Verdict + Issues at Top

**Current order:** Mechanical → Storytelling → Prompt Redundancy → Compaction → Auto-Checker → Additional → Verdict → Actionable Issues

**New order:**
1. Verdict (Section 1)
2. Actionable Issues Surfaced (Section 2)
3. Mechanical Design Critique (Section 3)
4. Storytelling Design Critique (Section 4)
5. Prompt Redundancy Analysis (Section 5)
6. Compaction Capabilities Report (Section 6)
7. Auto-Checker Failures (Section 7)
8. Additional Observations (Section 8)

**Table of Contents update:** Reflect new numbering and order.

**Output format:** Keep the YAML front matter at the very top. The body starts after the front matter with Section 1 (Verdict).

### 2.2 Expand Section 3 (Mechanical Design Critique) — New Pipeline-Specific Subsections

The rubric already has a "Mechanic Placement" subsection. We need to add explicit evaluation criteria for each narrative mechanic within each pipeline's critique. Add these as required subsections under each pipeline's "What Went Poorly" / "Issues" area:

#### 2.2.1 Rules Pipeline — Directive & Momentum

Under the Rules pipeline's Issues subsection, require:

- **Directive accuracy:** Does the directive match the band? `crit_fail` directives should describe catastrophic failure, not minor setbacks. `success` directives should not introduce costs. Cite turns where directive and band diverge.
- **Momentum delta correctness:** For each roll, verify `apply_momentum()` applied the correct delta from `MOMENTUM_DELTA`. Cite before/after momentum values. Flag any turn where momentum didn't move or moved in the wrong direction.
- **Difficulty selection:** Did the rules LLM pick a reasonable difficulty? Flag turns where difficulty seems disconnected from the fiction.

#### 2.2.2 Narrate Pipeline — Directive Binding & Tone

Under the Narrate pipeline's Issues subsection, require:

- **Directive binding:** Did the narration honor the band's directive? A `crit_fail` directive saying "Something precious is lost" that produces a cheerful outcome is a failure. A `partial` directive saying "succeed but at a cost" that produces a clean success is a failure.
- **Momentum tone:** Did the narration tone reflect momentum? At +2+: should feel like a strong run. At -2-: should offer breathing room unless fiction demands otherwise. Flag turns where tone contradicts momentum.
- **GM beat consumption:** When `pending_gm_beat` was present, did the narration surface it? A beat that's stored but never narrated is a consumption failure.
- **Pressure tone:** Did narration reflect active pressure? 3+ immediate pressures should feel overwhelming. 1+ building should show background tension. Flag turns where pressure is absent from narration despite being in state.
- **Deescalation respect:** When `deescalate > 0`, did the narration avoid adding new pressures or complications? A deescalation turn that introduces fresh threats is a failure.

#### 2.2.3 Scene Extract Pipeline — Scope Adherence

Under the Scene Extract pipeline's Issues subsection, require:

- **Scope adherence:** Scene extractor should ONLY emit: `npc_add/remove/update`, `compendium_npc_update`, `location_change`, `location_description`, `scene_tags`, `scene_tagline`. Flag any emission of `scene_pressure_*`, `gm_beat`, `inventory_*`, or `pc_condition_*` as a scope violation.
- **NPC grounding:** Are all `npc_add` entries referencing NPCs from the compendium or clearly introduced by the narration? Flag unsanctioned NPC introductions.
- **Location accuracy:** Does `location_change` only fire when the narration indicates a genuine location change? Flag false location changes (e.g., same room described differently).

#### 2.2.4 State Extract Pipeline — Stakes/Band Routing

Under the State Extract pipeline's Issues subsection, require:

- **Stakes honored:** When `stakes` named a condition (e.g., "wounded") and `band` was `setback`/`fail`/`crit_fail`, was the condition extracted? Flag turns where stakes named a cost but no corresponding `pc_condition_add` appeared.
- **Band-consistent extraction:** Does the state extraction match the band? A `crit_fail` should produce more severe consequences (multiple conditions, item loss) than a `partial`. Flag turns where band severity doesn't match extraction severity.
- **Condition dedup:** Are duplicate conditions properly deduplicated? Flag turns where the same condition appears twice.

#### 2.2.5 Progress Extract Pipeline — Full Narrative Mechanics

This is the most critical expansion. Under the Progress Extract pipeline's Issues subsection, require evaluation of ALL narrative mechanics:

**A. Scene Pressure Lifecycle:**
- **Add correctness:** New pressures should only appear when fiction justifies: named NPC/faction acts off-screen, quest deadline triggers, failed roll consequence activates, or world-state change creates threat. Flag pressures added for vague ambient danger or things already narratively resolved.
- **Update correctness:** Every `scene_pressure_update` ID must match an existing pressure. Flag updates with invented IDs.
- **Remove correctness:** Pressures should be removed when narratively resolved. Flag turns where resolved pressures persist.
- **Urgency escalation:** After pressure is added, verify that urgency escalates per engine thresholds: `background → building` at 6 turns, `building → immediate` at 10 turns. Flag pressures that stay at low urgency across many turns.
- **Expiry:** Pressures with `max_turns` should be removed when elapsed turns exceed the limit. Flag expired pressures that persist.
- **Purge on location change:** When player changes location, all `background` pressures should be purged. Flag background pressures that survive a location change.
- **Purge on combat end:** When combat ends, all `immediate` pressures should be purged. Flag immediate pressures that survive combat end.

**B. GM Beat Lifecycle:**
- **Generation quality:** Beats should only be emitted when fiction justifies: named NPC reacts, thread escalates, offscreen consequence surfaces, or relief is earned. Flag beats emitted for routine action or vague situations.
- **Instruction grounding:** `gm_beat.instruction` must reference a specific named entity (NPC id or pressure id) already in state. Flag beats that reference invented entities.
- **Instruction quality:** Instructions should be ≥40 characters and not start with filler prefixes ("something happens", "give the player"). Flag weak instructions.
- **Carry disposition:** When `beat_disposition == "carry"` and no new beat is emitted, `pending_gm_beat` should persist to the next turn. Flag carried beats that disappear.
- **Replace disposition:** When `beat_disposition == "replace"` and a new beat is emitted, the new beat should supersede the carried one. Flag replace failures.
- **Consume disposition:** When `beat_disposition == "consume"` (default), `pending_gm_beat` should be cleared after narration. Flag beats that persist after consume.
- **TTL expiry:** `beat_expires_turn = turn_no + 2` is a hard ceiling. Beats past their TTL should be nullified before narration. Flag beats that survive past their TTL.
- **Max one beat:** Only one `pending_gm_beat` should exist at a time. Flag accumulation.

**C. Quest Lifecycle:**
- **Band-gated completion:** Quest objectives should only complete when the band permits. A `crit_fail` should not complete a quest objective. Flag band-inconsistent quest updates.
- **Stall detection:** Stalled quests (3+ turns) should trigger `quest_ages` signal to progress extractor. Flag quests that stall without the signal.
- **Completion narrative:** Completed quests should have a corresponding `recent_events_add` entry. Flag completed quests without narrative documentation.

**D. Recent Events Ring Buffer:**
- **Ring buffer limit:** `recent_events` should not exceed 20 entries. Flag buffer overflows.
- **Deduplication:** Duplicate event IDs should not accumulate. Flag duplicate `recent_events_add` entries.
- **Compaction alignment:** After compaction, `recent_events` should not contain events already covered by compaction bullets. Flag deduplication misses.

**E. Action Suggestions:**
- **Relevance:** `actions` should suggest 4 choices grounded in current state (active quests, present NPCs, current location, recent events). Flag generic or irrelevant suggestions.
- **Variety:** Suggestions should cover different approaches (combat, social, exploration, movement). Flag homogeneous suggestions.

### 2.3 Expand Section 4 (Storytelling Design Critique) — New Criteria

Add the following new criteria to the storytelling section, with explicit scoring instructions:

#### 2.3.1 `momentum_arc` (existing, but expand)

**Current text** (lines 258-266) is good but needs engine constant references.

**Add:** Reference `MOMENTUM_MIN = -3`, `MOMENTUM_MAX = +3`, and `MOMENTUM_DELTA` table. Require the judge to plot momentum across all turns and assess:
- Did momentum reach meaningful extremes (±2 or beyond)?
- Did the momentum arc have a shape (rising, peaking, resolving) or was it flat/erratic?
- Did momentum tone correlate with narration tone?
- A momentum field that barely moves across 10 turns scores 1-2.

#### 2.3.2 `pressure_arc` (NEW)

Did the scene pressure system produce a felt dramatic shape across the session — rising tension toward a peak, followed by resolution or a meaningful cliffhanger?

**Mechanical checks:**
- Plot all pressure entries across turns: when added, urgency level, when removed/escalated.
- Did pressures escalate correctly? `background → building` at 6 turns, `building → immediate` at 10 turns.
- Did `urgency: immediate` pressures produce visibly higher-stakes narration?
- Did expired pressures (`max_turns` elapsed) disappear from state?
- Did location changes purge `background` pressures?
- Did combat end purge `immediate` pressures?
- A pressure system where entries sit inert across 10 turns without escalation scores 1-2.

Score the session-level shape, not individual turn pacing.

#### 2.3.3 `beat_lifecycle` (NEW)

Did GM beats function as effective storytelling devices across turns?

**Mechanical checks:**
- **Generation rate:** Were beats emitted at a reasonable frequency (not every turn, not never)? Flag beats emitted for routine action.
- **Consumption rate:** Were stored beats surfaced in narration within 1-2 turns? Flag beats that sat in `pending_gm_beat` for 3+ turns without being narrated.
- **Carry behavior:** When `beat_disposition == "carry"`, did the beat persist and eventually get surfaced? Flag carried beats that were silently dropped.
- **TTL enforcement:** Did beats expire at `turn_no + 2`? Flag beats that survived past TTL.
- **Instruction quality:** Were beat instructions specific and grounded in existing entities? Flag generic beats ("something happens") or beats referencing invented entities.
- **Narrative impact:** Did surfaced beats create meaningful story moments (complications, revelations, opportunities, breathing room)? Flag beats that had no observable effect on narration.

Score based on the proportion of beats where all checks above pass. A session with no beats scores this criterion N/A.

#### 2.3.4 `directive_narration_binding` (NEW)

Did the rules engine's directives bind to the narrator's output as intended?

**Mechanical checks:**
- For each turn with a dice roll, verify the narration's outcome matches the roll band and directive:
  - `crit_fail`: catastrophic failure, real loss
  - `fail`: outright failure, complication
  - `setback`: resource spent, time lost, new problem
  - `partial`: success at a cost
  - `success`: clean success
  - `crit_success`: outstanding success, unexpected benefit
- A `crit_fail` that produces a cheerful narrative is a failure regardless of prose quality.
- A `partial` that produces no cost or complication is a failure.
- A `success` that introduces unexpected costs is a failure.

Score based on the proportion of rolls where the narration matches the band/directive. A run with no rolls scores N/A.

#### 2.3.5 `stakes_routing` (NEW)

Did the stakes/band routing from rules to extractors produce mechanically consistent consequences?

**Mechanical checks:**
- When `stakes` named a condition and `band` was `setback`/`fail`/`crit_fail`, was the condition extracted by state extractor?
- When `stakes` named a consequence and `band` was `crit_fail`, was a `scene_pressure_add` emitted by progress extractor?
- When `stakes` named a consequence and `band` was `crit_success`, was an `opportunity` or `escalation` beat considered?
- Flag turns where stakes were named but no mechanical consequence followed.

Score based on the proportion of rolls where stakes routing produced observable mechanical consequences.

#### 2.3.6 `deescalation_mechanics` (NEW)

Did deescalation work as a pressure-resolution mechanic?

**Mechanical checks:**
- When `deescalate > 0` (success/crit_success on active pressure), did the narration avoid adding new pressures?
- When `deescalate >= 0.8` (success on immediate pressure), was a `breathing_room` beat type preferred or no beat emitted?
- When `deescalate >= 1.0` (crit_success on immediate pressure), were new pressures suppressed entirely?
- Flag turns where deescalation was active but new pressures were added.

Score based on the proportion of deescalation turns where the mechanic was respected.

### 2.4 Update Mechanic Placement Table

**Current table** (lines 127-140) needs updating to reflect post-overhaul state:

| Field | Correct stream | Violation if seen in wrong stream |
|---|---|---|
| `npc_add`, `npc_remove`, `npc_update`, `compendium_npc_update` | scene | — |
| `location_change`, `location_description` | scene | — |
| `scene_tags`, `scene_tagline` | scene | — |
| `inventory_add`, `inventory_remove`, `inventory_update` | state | — |
| `pc_condition_add`, `pc_condition_remove` | state | — |
| `quest_updates` | progress | — |
| `recent_events_add`, `recent_events_update`, `recent_events_remove` | progress | — |
| `scene_pressure_add` | progress | Flag if emitted by scene |
| `scene_pressure_remove` | progress | Flag if emitted by scene |
| `scene_pressure_update` | progress | Flag if emitted by scene; also flag if id not in existing pressure list |
| `gm_beat` | progress | Flag if emitted by scene |
| `beat_disposition` | progress | — |
| `actions`, `outcome_summary` | progress | — |

**Changes from current:**
- Added `location_description` to scene stream
- Changed `scene_pressure_add` from "scene" to "progress"
- Changed `scene_pressure_remove` from "scene" to "progress"
- Changed `scene_pressure_update` from "scene" to "progress"
- Changed `gm_beat` from "progress (via meta)" to "progress" (it's a direct field on ProgressExtractResult, not via meta)
- Added `beat_disposition` to progress stream

### 2.5 Update Storytelling Criterion Weights

**`pacing_and_pressure`** (lines 246-256): Currently 60% pressure_mechanics + 40% narrative_pacing.

**Update:** Since `pressure_arc` is now its own criterion, change `pacing_and_pressure` to focus purely on narrative pacing (breathing room, momentum tone, arc satisfaction). The mechanical pressure component moves to the new `pressure_arc` criterion.

**New `pressure_arc`** gets its own standalone score (1-5) with the mechanical checks from section 2.3.2.

### 2.6 Update Output Format

**New section numbering:**
```
Section 1: Verdict
Section 2: Actionable Issues Surfaced
Section 3: Mechanical Design Critique
  Pipeline: rules
  Pipeline: narrate
  Pipeline: extract_scene
  Pipeline: extract_state
  Pipeline: extract_progress
Section 4: Storytelling Design Critique
  Criterion: quest_arc_quality
  Criterion: rewards_and_consequences
  Criterion: narrative_compellingness
  Criterion: npc_development
  Criterion: world_consistency
  Criterion: player_agency
  Criterion: consequence_persistence
  Criterion: pacing_and_pressure
  Criterion: momentum_arc
  Criterion: pressure_arc (NEW)
  Criterion: beat_lifecycle (NEW)
  Criterion: directive_narration_binding (NEW)
  Criterion: stakes_routing (NEW)
  Criterion: deescalation_mechanics (NEW)
Section 5: Prompt Redundancy Analysis
Section 6: Compaction Capabilities Report
Section 7: Auto-Checker Failures
Section 8: Additional Observations
```

---

## Part 3: Implementation Steps

### Step 1: Update ARCHITECTURE.md

Apply all fixes from Part 1 above. This is a pure documentation update — no code changes.

**Verification:** Read through the updated ARCHITECTURE.md and confirm:
- Step 2a (Scene Extract) shows only: scene_tags, scene_tagline, location_change, location_description, npc_add/remove/update, compendium_npc_update
- Step 2c (Progress Extract) shows: quest_updates, recent_events_add/update/remove, actions, outcome_summary, gm_beat, beat_disposition, scene_pressure_add/remove/update
- Step 2c "Always runs" note correctly describes progress as the source of scene_pressure and pending_gm_beat
- Diagrams match the table descriptions

### Step 2: Update Rubric — Structure

Apply all fixes from Part 2.2 (restructure), Part 2.4 (mechanic placement table), Part 2.5 (criterion weights).

### Step 3: Update Rubric — New Sections

Apply all fixes from Part 2.3 (new storytelling criteria) and Part 2.2 (expanded pipeline-specific subsections).

### Step 4: Update Output Format

Apply the new section numbering from Part 2.6 to the "Output format" section at the bottom of the rubric.

---

## Tradeoffs and Decisions

1. **Granularity of mechanical checks:** The rubric now has very specific mechanical checks (e.g., "background → building at 6 turns"). This is intentional — the judge has access to engine constants via the ARCHITECTURE.md context. If the judge model is weak, these specific checks may produce inconsistent results. Mitigation: the checks are framed as "flag if" rather than "must always", allowing the judge discretion.

2. **New criteria count:** We're adding 5 new storytelling criteria (pressure_arc, beat_lifecycle, directive_narration_binding, stakes_routing, deescalation_mechanics). This makes the rubric quite long. Mitigation: each criterion is self-contained and the judge can score N/A for criteria where the relevant mechanic didn't fire.

3. **Report reorganization:** Moving verdict to the top changes the flow from "detailed analysis → conclusion" to "conclusion → detailed analysis". This is more useful for quick review but may feel abrupt. The YAML front matter still provides the scores at the very top.

4. **ARCHITECTURE.md eval context region:** The `<!-- EVAL_CONTEXT_START -->` ... `<!-- EVAL_CONTEXT_END -->` region is what gets fed to the judge. All changes to the architecture doc within this region directly affect what the judge evaluates. Changes outside this region (like the mermaid diagrams) don't affect the judge but should still be accurate for human readers.

---

## Files Changed

| File | Change Type | Summary |
|---|---|---|
| `docs/ARCHITECTURE.md` | modify | Fix Scene/Progress extract descriptions, diagrams, and data flow to reflect post-overhaul state |
| `evals/rubrics/default.md` | modify | Restructure (verdict first), add 5 new storytelling criteria, expand pipeline-specific checks, update mechanic placement table, update output format |
