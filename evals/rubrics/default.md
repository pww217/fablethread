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
- [Mechanical Design Critique](#mechanical-design-critique)
- [Storytelling Design Critique](#storytelling-design-critique)
- [Prompt Redundancy Analysis](#prompt-redundancy-analysis)
- [Compaction Capabilities Report](#compaction-capabilities-report)
- [Auto-Checker Failures](#auto-checker-failures)
- [Additional Observations](#additional-observations)
- [Verdict](#verdict)
- [Actionable Issues and Remediations](#actionable-issues-and-remediations)


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


## Section 1: Mechanical Design Critique (PRIMARY — weighted 2x)


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
  `gm_beat` is documented to live in scene; if you see it being emitted by
  progress, that's misplacement.)
- Would this mechanic produce better results if surfaced earlier (e.g. before
  narration) or later (e.g. as a delta post-validate)?
- Should this mechanic's input source be different? (e.g. should the state
  extractor receive `recent_events` to dedupe condition IDs against prior
  turns?)\

If you find a misplaced mechanic, write a clear remediation: which pipeline it
belongs in, what data flow needs to change.


### Issues
A bulleted list. For each issue:
- **<short description>** (turns: <list>) — Failure mode: `<bad prompt | failed
  to output key information | failed to input key information | messy logic |
  scope/domain mismatch | schema drift | misplaced mechanic | wasted tokens>`.
  Remediation: <what should change>.


### Pipeline Score (1-5)


Major mechanical failures (scope errors, extraction mismatches, dice-narration
contradictions, misplaced mechanics) cap the score at 1 or 2 for that pipeline.


---


## Section 2: Storytelling Design Critique (SECONDARY)


The narrative quality serves as a check on whether the mechanics are producing
good fiction. A 5/5 story built on broken extraction is a false positive.


For each of the narrative criteria below, score 1-5 with two or more
sentences and citations to specific turns:


### quest_arc_quality
Did quests form a compelling long arc? Did completing or failing them feel
earned and create interesting consequences?


### rewards_and_consequences

Did the game give real rewards for success and real consequences for failure?
Score this criterion by grounding it in observable mechanics — not narrative
feel alone. For each turn where a roll occurred, check the following:

**Roll directive honored:** Did the narration's outcome match the roll `band`
and `directive`? A `crit_fail` that produces a cheerful narrative is a failure
here regardless of prose quality. A `partial` that produces no cost or
complication is also a failure.

**Momentum moved correctly:** Did `pc.momentum` change in the direction the
roll band implies? The engine defines momentum deltas per band (e.g.
`crit_success` → +2, `fail` → −1, `crit_fail` → −2, `partial` → ±0 or −1
depending on config). Cite the turn, the band, and the before/after momentum
value. Flag any turn where momentum did not move or moved in the wrong direction.

**Conditions applied for costs:** When the roll band was `partial` or worse and
the `directive` specified a cost, check whether a `pc_condition_add` was
extracted on that turn or the immediately following turn. A partial success with
no cost extracted and no condition added is a soft failure of the consequence
system.

**gm_beat influence:** When a `gm_beat` was emitted (check the scene extract
output for a non-null `gm_beat.instruction`), verify that the *next* turn's
narration shows observable influence from it — a complication surfaced, a
revelation revealed, an opportunity created, or breathing room given. A
`gm_beat` that fires but produces no downstream narrative effect is a mechanic
that is working structurally but failing functionally.

Score based on the proportion of rolls where all four checks above pass. A run
with no rolls scores this criterion N/A and should be noted.


### narrative_compellingness
Was the overall story compelling enough to keep playing? Did choices matter?


### npc_development
Did NPCs evolve and react meaningfully across turns?


### world_consistency
Were all entities (NPCs, locations, items) that appeared in narration sanctioned
by the engine, worldpack, or player input? Flag any unsanctioned introductions —
invented NPCs, unregistered locations, items with no extraction grounding. This
is a trust axis distinct from how existing NPCs are developed.


### player_agency
Did the game respect player choice? Did failures create new options rather
than dead-ends? Did the engine honor the player's stated action rather than
redirecting or reinterpreting it?


### consequence_persistence
Did the consequences of rolls — especially failures and partials — carry forward
into subsequent turns? Anchor this to mechanics: check whether `pc_condition`
entries added on a cost turn are still present in the state snapshot 2–3 turns
later (or were explicitly removed with a corresponding narrative justification).
Check whether `scene_pressure` entries added as a result of a failure escalate
correctly per the engine's urgency thresholds (`background` → `building` →
`immediate`) rather than sitting inert. A condition that silently disappears or a
pressure that never escalates is a persistence failure. Score the session as a
whole.


### pacing_and_pressure
Combined score, internally weighted 60% pressure_mechanics (objective —
escalation, expiry, urgency reflected in narration) + 40% narrative_pacing
(subjective — breathing room, momentum tone, arc satisfaction).

For the pressure_mechanics component, check: did `scene_pressure` entries with
`urgency: immediate` produce visibly higher-stakes narration on those turns? Did
`urgency: building` pressures appear in the narration as background tension
before escalating? Did expired pressures (`max_turns` elapsed) disappear from
state? Cite specific pressure IDs and turns.


### momentum_arc
Did the pressure and momentum system produce a felt dramatic shape across the
session — rising tension toward a peak, followed by resolution or a meaningful
cliffhanger? For the mechanical component: plot `pc.momentum` across all turns
from the state snapshots and describe whether the arc had a clear shape (rising,
peaking, resolving) or was flat/erratic. A momentum field that barely moves
across 10 turns, or oscillates randomly with no narrative correlation, is a
score of 1–2 regardless of whether individual turns felt tense. Score the
session-level shape, not individual turn pacing.


---


## Section 3: Prompt Redundancy Analysis


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


## Section 4: Compaction Capabilities Report


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
- After T6: turns 1–3 are compacted into bullets, turns 4–6 are kept as recent
  narrative. Expect **3 bullets covering T1–T3**.
- At T12: turns 7–11 are compacted into bullets, turns 9–12 are kept as
  recent narrative. Expect **5 additional bullets covering T7–T11**.
- The engine always retains the 3 most recent turns as full narrative plus
  all compacted bullets for older turns.


**Expectations for typical eval runs:** Most eval runs are 10 turns. With
`compact_every=6` the compactor fires at T6 only (T12 is beyond the run).
In T7 (it runs between 6 and 7) you should see **3 bullets covering T1–T3** and turns 4–6 kept as
recent narrative. This is correct behavior. Do not penalize the engine for
not compacting at T7–T10 — the compactor only fires at multiples of
`compact_every`. Do not penalize for having only 3 bullets — that is the
expected output for a 10-turn run.


**What correct compaction output looks like:** When the compactor fires at T6,
evaluate all three of the following:

1. **Narrative bullets:** T1–T3 should be represented as concise summary
   bullets in `chronicle.md`. Each bullet must faithfully represent the key
   event or player action of that turn. A bullet that misrepresents, inverts, or
   omits a named entity (NPC name, item name, location name, quest ID) from the
   turn it covers is a compaction failure. A bullet that is generic enough to
   apply to any turn ("the player took an action") is also a failure.

2. **recent_events deduplication:** After compaction, `scene.recent_events`
   should not contain events whose content is already covered by a compaction
   bullet. The compactor is expected to consolidate overlapping `recent_events`
   entries into fewer, denser records via `recent_events_compact`. Check the
   applied sanitization in the Deterministic Signals block: if
   `recent_events_compact` is empty but `recent_events` contains 5+ entries
   spanning T1–T3, that is a deduplication miss.

3. **Stale state sanitization:** The compaction pass should close completed or
   failed quests, remove resolved conditions, and remove expired pressures from
   state. Check the `CompactorSanitizationResult` fields (`quest_close`,
   `condition_remove`, `pressure_remove`, `inventory_remove`) against the state
   snapshot at T6. Any obviously stale entry — a quest that was narratively
   resolved but not closed, a condition that expired narratively but persists in
   state — is a sanitization miss.


If compaction did not fire (run was too short), state that and skip the per-
capability evaluation for this run.


If compaction fired but produced low-quality bullets (per criteria 1 above),
score the `extract_progress` pipeline lower in Section 1.


---


## Section 5: Auto-Checker Failures


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


## Section 6: Additional Observations


Patterns or bugs that did not fit into the structured sections above. Always
present; may be `None.`.


---


## Section 7: Verdict


2-4 sentences. Concrete, specific, actionable. Reference turn numbers. Justify
why mechanical_score diverges from narrative_score if applicable. End with the
single most important fix the engine needs.


---


## Section 8: Actionable Issues Surfaced


A paragraph per issue that arose during this evaluation, and a recommendation
to fix or resolve it. Place them in appropriate major, minor, trivial categories
and prefix each with the type of issue: `[Engine]`, `[Prompting]`,
`[Consistency]`, etc.

Each issue must also carry one of the following mechanical tags where
applicable: `bad prompt | failed to output key information | failed to input key
information | messy logic | scope/domain mismatch | schema drift | misplaced
mechanic | wasted tokens`.

---


## Output format


Return the response as a YAML front matter block followed by the markdown body
in the structure described above. Use this exact front matter shape:


```yaml
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
```


Then produce the full markdown body using this structure:

Table of Contents

<list all sections below with relative path hyperlinks>
ie Verdict
Mechanical Design Critique
Pipeline: rules

... <subsections from Section 1> ...
Pipeline: narrate

...
Pipeline: extract_scene

...
Pipeline: extract_state

...
Pipeline: extract_progress

...
Storytelling Design Critique
Criterion: quest_arc_quality

Score: <1-5>
<two or more sentences with turn citations>
Criterion: rewards_and_consequences

Score: <1-5>
<structured per-roll breakdown: band, directive honored, momentum delta, condition extracted, gm_beat downstream effect>
Criterion: narrative_compellingness

...
Criterion: npc_development

...
Criterion: world_consistency

Score: <1-5>
<two or more sentences with turn citations>
Criterion: player_agency

...
Criterion: consequence_persistence

Score: <1-5>
<condition persistence check + scene_pressure escalation check with turn citations>
Criterion: pacing_and_pressure

...
Criterion: momentum_arc

Score: <1-5>
<momentum value plot across turns + arc shape assessment>
Prompt Redundancy Analysis

...
Compaction Capabilities Report

...
Auto-Checker Failures

...
Additional Observations

...
Verdict

...
Actionable Issues and Remediations
Major

...
Minor

...
Trivial

...
