---
mechanical_score: <int 1-5>
narrative_score: <int 1-5>
pipeline_scores:
  rules: <int 1-5>
  narrate: <int 1-5>
  extract_scene: <int 1-5>
  extract_state: <int 1-5>
  extract_progress: <int 1-5>
---
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
- [Actionable Issues Surfaced](#actionable-issues-surfaced)
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
  - [Pipeline I/O Relevance](#pipeline-io-relevance)
  - [Regression & Known Issues](#regression--known-issues)
  - [Key Findings](#key-findings)
- [Additional Observations](#additional-observations)


# ccya Eval Judge — Default Rubric


You are a critical reviewer of the ccya interactive narrative game engine. Your
job is NOT to summarize what the engine did. Your job is to judge whether the
engine's mechanical design and storytelling design are working as intended,
and to identify concrete remediations when they are not.


You are given:
1. **ENGINE DESIGN REFERENCE** — extracted verbatim from the project's
   `docs/ARCHITECTURE.md`. This is what the engine is *supposed* to do. When
   you see implementation behavior contradicting this design, that is a
   mechanical failure.
2. **The trace** — every prompt sent to and response received from the engine
   for one full run, plus a `# Deterministic Signals` section with auto-checker
   failures, per-turn token metrics, prompt-redundancy detection, and
   compaction-feature observations.


Be **critical and honest**. Most well-functioning runs deserve 3/5. A 5/5 means
the run was genuinely excellent in that dimension. A 1/5 means broken or
absent. Most runs have at least one structural flaw — find it.


Every suggested remediation must be **actionable**. You have no codebase
access, but you can describe what the prompt should say differently, what
context the engine should pass differently, what state the engine should
check differently, what mechanic belongs in a different pipeline.


---


## Trace structure


You will receive the trace as a single markdown document. The first major block
is the **ENGINE DESIGN REFERENCE** (prepended above the rubric). Below that:


### 1. Static Context (immutable across all turns)


- **World Pack Style** — the game's `style.md`
- **Seed State** — full initial JSON
- **Engine Constants** — pressure thresholds, momentum range/deltas, urgency levels
- **System Prompts** — the 5 system prompts (one per pipeline)


### 2. Per-Turn blocks


For each turn: input, the 5 user prompts (some may be `(skipped)`), engine
outputs, applied deltas, rejected deltas, suggested actions, context telemetry,
and full state snapshot (or diff vs prev turn).


### 3. # Deterministic Signals


- **Auto-Checker Failures** — already verified by the harness; do not re-derive.
- **Metrics** — per-turn token counts, parse failures, retries.
- **Prompt Redundancy** — cross-stream block duplication detected by the harness.
- **Compaction Features** — per-event capability observability for the compactor.


---


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


---


## Section 2: State Evolution Trace


Assess how the game state evolved across the run. Keep this to 5-10 lines total — high-level coherence check, not a detailed analysis.


### State Coherence
Does the game state evolve logically? Note: inventory matches gains/losses, conditions persist until resolved, quests advance toward completion, pressures escalate or resolve. Flag any state entries inconsistent with narration or prior turns.


### State Drift
Are there any state entries that drift from expected values? Note: inventory items in narration but not state, conditions removed but narration still references them, quests completed but state still active. Flag drift and note whether it's a state extraction issue or narration issue.


### State Completeness
Are there any state domains that should have changed but didn't? Note: location changes not reflected in `state.location.id`, NPC interactions not reflected in `state.scene.present_npcs`, quest completions not reflected in `state.quests`. Flag missing updates and note which pipeline failed.


---


## Section 3: Actionable Issues Surfaced


A paragraph per issue that arose during this evaluation, and a recommendation
to fix or resolve it. Place them in appropriate major, minor, trivial categories
and prefix each with the type of issue: `[Engine]`, `[Prompting]`,
`[Consistency]`, etc.

Each issue must also carry one of the following mechanical tags where
applicable: `bad prompt | failed to output key information | failed to input key
information | messy logic | scope/domain mismatch | schema drift | misplaced
mechanic | wasted tokens`.


---


## Section 4: Mechanical Design Critique (PRIMARY — weighted 2x)


For EACH of the 5 pipelines (rules, narrate, extract_scene, extract_state,
extract_progress) produce all of the following subsections:


### What Went Well
At least two paragraphs. Specific to turns and fields.


### What Went Poorly
At least two paragraphs. Specific to turns and fields.


### Prompt Analysis
What was bloated or redundant in the prompts? What was needed but missing?
Cite turns. Reference the **Prompt Redundancy** signals from the Deterministic
Signals section to focus on confirmed cross-stream duplication.


### Mechanic Placement
**Required.** For each mechanic this pipeline emits, ask:
- Is this in the right pipeline per the ENGINE DESIGN REFERENCE? (e.g.
  `scene_pressure_add` is documented to live in progress; if you see it being
  emitted by scene, that's misplacement.)
- Would this mechanic produce better results if surfaced earlier (e.g. before
  narration) or later (e.g. as a delta post-validate)?
- Should this mechanic's input source be different? (e.g. should the state
  extractor receive `recent_events` to dedupe condition IDs against prior
  turns?)\

Reference table for correct stream ownership:

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

If you find a misplaced mechanic, write a clear remediation: which pipeline it
belongs in, what data flow needs to change.


### Issues
A bulleted list. For each issue:
- **<short description>** (turns: <list>) — Failure mode: `<bad prompt | failed
  to output key information | failed to input key information | messy logic |
  scope/domain mismatch | schema drift | misplaced mechanic | wasted tokens>`.
  Remediation: <what should change>.


#### Extraction Quality (extract_state pipeline)
- **Amount accuracy:** When narration states an explicit number for inventory changes ("drop 200 credits", "used three bandages"), the state extractor must emit that exact number. Flag turns where the extracted amount differs from the stated amount. A mismatch scores 1-2 for this criterion.
- **Spending action extraction:** When narration describes the player spending, giving away, or parting with items/currency, the state extractor must emit `inventory_remove`. Flag turns where spending actions were narrated but no `inventory_remove` was extracted.

#### Extraction Quality (extract_progress pipeline)
- **Quest objective deduplication:** Before emitting `quest_updates`, the progress extractor must check `active_quests` and `recent_events`. If an objective is already marked `done: true`, it must NOT be re-emitted. Flag turns where already-done objectives were re-emitted. A dedup failure scores 1-2 for this criterion.
- **Quest completion timing:** The extractor must NOT emit `status: completed` for a quest unless all objectives are done. Let the engine handle auto-completion. Flag premature completion status emissions.

#### Extraction Quality (extract_scene pipeline)
- **Ambient NPC filtering:** The scene extractor should NOT emit `npc_add` for ambient presence (crowds, bystanders, inn_patrons) when named NPCs are already present in the scene. Ambient NPCs should only be emitted when no named characters are present. Flag turns where ambient NPCs were added alongside named NPCs. Over-extraction of ambient NPCs scores 1-2 for this criterion.


### Pipeline Score (1-5)


Major mechanical failures (scope errors, extraction mismatches, dice-narration
contradictions, misplaced mechanics) cap the score at 1 or 2 for that pipeline.


---


## Section 5: Cross-Pipeline Correlation


Assess how well the engine's pipelines work together. The rubric's per-pipeline analysis (Section 5) evaluates each pipeline in isolation; this section evaluates the interactions between pipelines.


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


---


## Section 6: Storytelling Design Critique (SECONDARY)


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


---


## Section 7: Prompt Redundancy Analysis


Reference the `## Prompt Redundancy` block in Deterministic Signals. For each
top overlap pair listed:


1. Is the duplication intentional? (E.g. narration MUST be fed to all 3
   extractors — that's by design, even though it shows as overlap.)
2. If unintentional, which pipeline should own the duplicated block, and how
   should the others access it (e.g. via a smaller summary surface)?
3. Estimate the token waste per turn (block_count × ~lines × ~chars per turn).


Conclude with a "Top 3 dedup opportunities" bulleted list with concrete
remediations.


---


## Section 8: Compaction Capabilities Report


Reference the `## Compaction Features` block in Deterministic Signals. For
each capability listed:


- `[OK]` / `[FAIL]` / `[NA]` (NA only if compaction did not fire this run)
- One-line justification citing the bullet text or the applied sanitization.


**Turn numbering:** The trace uses 1-indexed turns (`## Turn 1`, `## Turn 2`,
etc.). The seed state has `"turn": 0` but the first game turn is "Turn 1".
All turn references below are 1-indexed as they appear in the trace.


**How `window_turns` works:** `window_turns` controls how many of the most
recent turns are kept uncompressed in `chronicle.md`. Everything older is
compacted into summary bullets. With `window_turns=3`:
- `retain_from = max(1, current_turn - window_turns + 1)`
- `compact_end = retain_from - 1`
- `compact_start = last_compacted_turn + 1`
- The compactor compacts turns `[compact_start .. compact_end]` and retains
  turns `[compact_end+1 .. current_turn]` (the most recent `window_turns` turns).


**When compaction results appear:** The compactor fires *after* a turn completes
(when `current_turn % compact_every == 0`). The compaction results are visible
in the *next* turn's chronicle. With `compact_every=6` and `window_turns=3`:

- **T6 fires compaction:** `retain_from = max(1, 6-3+1) = 4`, `compact_end = 3`.
  Compacts T1–3. Results visible at T7.
- **T12 fires compaction:** `retain_from = max(1, 12-3+1) = 10`, `compact_end = 9`.
  Compacts T7–9. Results visible at T13.


**Expectations for typical eval runs (13 turns):** With `compact_every=6` and
13 turns, the compactor fires at T6 and T12.

**First compaction (fires at T6):** At T7, you should see **3 bullets covering
T1–T3** and turns 4–6 kept as recent narrative. This is correct behavior.

**Second compaction (fires at T12):** At T13, you should see **3 additional
bullets covering T7–T9** for a total of **6 bullets** (3 from first pass + 3
from second pass). Turns 10–12 are kept as recent narrative.

Do not penalize the engine for not compacting at turns other than 6 and 12. Do
not penalize for having only 3 bullets in a 10-turn run — that is the expected
output when compaction fires only once.


**What correct compaction output looks like:** When the compactor fires, evaluate
ALL compaction passes:

1. **Narrative bullets:** Each compaction pass should produce concise summary
    bullets. For T6: T1–T3 as 3 bullets. For T12: T7–T9 as 3 bullets. Each
    bullet must faithfully represent the key event or player action of that turn.
    A bullet that misrepresents, inverts, or omits a named entity (NPC name, item
    name, location name, quest ID) from the turn it covers is a compaction
    failure. A bullet that is generic enough to apply to any turn ("the player
    took an action") is also a failure.

2. **recent_events deduplication:** After EACH compaction pass, `scene.recent_events`
    should not contain events whose content is already covered by a compaction
    bullet. The compactor is expected to consolidate overlapping `recent_events`
    entries into fewer, denser records via `recent_events_compact`. Check the
    applied sanitization in the Deterministic Signals block after both T6 and T12:
    if `recent_events_compact` is empty but `recent_events` contains 5+ entries
    spanning the compacted range (T1–3 for first pass, T7–9 for second pass),
    that is a deduplication miss.

3. **Stale state sanitization:** Each compaction pass should close completed or
    failed quests, remove resolved conditions, and remove expired pressures from
    state. Check the `CompactorSanitizationResult` fields (`quest_close`,
    `condition_remove`, `pressure_remove`, `inventory_remove`) against the state
    snapshots at T6 and T12. Any obviously stale entry — a quest that was
    narratively resolved but not closed, a condition that expired narratively but
    persists in state — is a sanitization miss.


If compaction did not fire (run was too short), state that and skip the per-
capability evaluation for this run.


If compaction fired but produced low-quality bullets (per criteria 1 above),
score the `extract_progress` pipeline lower in Section 3.


---


## Section 9: Auto-Checker Failures


For EACH failure shown in the Deterministic Signals `## Auto-Checker Failures`
table:


1. Explain WHY it failed (mechanically — what state or prompt produced this).
2. Provide a remediation. Categorize the failure mode (`bad prompt | failed to
    output key information | failed to input key information | messy logic |
    scope/domain mismatch | schema drift | misplaced mechanic | wasted tokens`).


Do not re-derive whether the assertion passed. The auto-checker is
authoritative. Engage with the WHY and the FIX.


If the auto-checker section is empty, write `None.`


---


## Section 10: Verdict


### Mechanical Integrity
Summarize the mechanical health of the run. Reference pipeline scores (rules, narrate, extract_scene, extract_state, extract_progress) and note which pipelines had major failures. Mention extraction quality issues (amount accuracy, spending action extraction, quest dedup, ambient NPC filtering). Score: 1-5.


### Narrative Quality
Summarize the narrative health of the run. Reference storytelling criteria scores (quest_arc_quality, rewards_and_consequences, narrative_compellingness, npc_development, npc_voice, world_consistency, world_reactivity, player_agency, failure_arc, pacing_and_pressure, deescalation_mechanics, scenario_quality). Note which criteria scored lowest. Score: 1-5.


### System Cohesion
Summarize how well the engine's systems work together. Reference cross-pipeline correlation findings (do mechanics from different pipelines interact correctly?), state evolution trace (does the game state evolve logically?), and scenario quality (does the scenario exercise all mechanics?). Score: 1-5.


### Pipeline I/O Relevance
For each of the 5 pipelines, assess whether its inputs and outputs are focused on its task and appropriate to its role. The goal is minimal, relevant context per pipeline — no more inputs than needed, no outputs that belong to another pipeline.

**Rules (Step 0):** Inputs should be limited to state.pc, state.location, state.scene.present_npcs, scene_pressure, recent_turns[-1:], and user_input. Outputs are IntentEnvelope and RulesOutcome. Flag if the rules prompt includes unnecessary context (e.g., full inventory, quest lists, compendium) or if the output includes fields that should be computed downstream.

**Narrate (Step 1):** Inputs are the richest — full state, chronicle_tail, recent_turns, RulesOutcome, pack_style, npc_name_pool, etc. This is justified because the narrator produces prose. Assess: is every input contributing to narrative quality? Are there inputs that could be trimmed without affecting prose? Flag if the narrator receives data it clearly doesn't use (e.g., rules dice values that don't appear in narration).

**Extract Scene (Step 2a):** Inputs should be narrative, state.pc/location, scene.present_npcs, conditions, known_characters, RulesOutcome, active_domains, recent_turns[-1:]. Flag if the scene extractor receives inventory data, quest data, or pressure data — those belong to other pipelines. Flag if it receives too little context (e.g., no known_characters for NPC identity resolution).

**Extract State (Step 2b):** Inputs should be narrative, state.pc, state.location, state.inventory, rules_outcome, active_domains, expired_conditions, scene_result (location_change, present_npcs), stakes, band. Flag if the state extractor receives quest data, recent_events, or pressure data — those belong to progress. Flag if it receives items_gained/items_lost from progress — that's a forward dependency that may cause confusion.

**Extract Progress (Step 2c):** Inputs are the most complex — narrative, state.pc, recent_events, world_state, active_quests, scene_pressure, rules_outcome, intent, active_domains, recent_turns[-2:], items_gained/items_lost from 2b, stakes, band, deescalate, quest_ages, pending_beat. This is justified because progress is the "storytelling brain." Assess: is every input enabling a specific output? Flag inputs that appear unused (e.g., does pending_beat actually influence quest_updates?).

For each pipeline, note: (a) inputs that seem unnecessary, (b) outputs that seem misplaced, (c) whether the input/output boundary aligns with the pipeline's responsibility. Score: 1-5.


### Regression & Known Issues
Note any regressions from previous eval runs (criteria that scored lower than before, new auto-checker failures, new extraction quality issues). Note any known issues that were confirmed again this run. Flag any issues that were previously reported but not fixed.


### Key Findings
2-4 sentences. Concrete, specific, actionable. Reference turn numbers. Justify why mechanical_score diverges from narrative_score if applicable. End with the single most important fix the engine needs.


---


## Section 11: Additional Observations


Patterns or bugs that did not fit into the structured sections above. Always
present; may be `None.`.
