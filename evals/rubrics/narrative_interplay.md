---
# narrative_score: int 1-5
# system_cohesion_score: int 1-5
---

# ccya Eval — Narrative & Mechanic Interplay Judge

You are evaluating whether the ccya engine's narrative output correctly reflects
and responds to its mechanical state. You are NOT auditing prompt architecture
or extraction schema correctness — those are handled by other judges.

Your trace contains:
- Narration text per turn (the actual prose shown to players)
- Rules output: roll band, directive, intent per turn
- Mechanic state fields per turn: momentum, GM beats, unified threads, conditions, NPCs
- State diffs (mechanic-relevant fields only)

Every finding must cite a specific turn and field.

Scoring philosophy:
- 5/5: Narration consistently honors directives, tone matches momentum, every beat/pressure
  creates observable story consequence.
- 3/5: Minor disconnects (1–2 turns), no systematic failures.
- 1–2/5: Directives routinely ignored, tone disconnected from momentum band, mechanics
  create no story consequence.

---

## HOW TO READ YOUR TRACE

Per-turn blocks contain:
- **Rules output**: `band`, `directive`, `intent`, `roll` (if present)
- **Narration**: the prose output
- **Extraction outputs**: scene (NPCs, location), state (inventory, conditions), storytell (unified threads, beats)
- **State diff**: changes to `meta.momentum`, `scene`, `pc.conditions`

You do NOT have access to the system or user prompts — do not comment on prompt architecture.

---

## SECTION 1 — Mechanic→Narrative Chain Analysis

### 1A — Rules Directive + PacingContext → Tone

For each turn with a roll:

| Turn | Band | Rules Directive | PacingContext.directive | Tone Match? | Evidence (quote ≤15 words) | Flag |
|------|------|-----------------|-------------------------|-------------|---------------------------|------|

Flag: `TONE_MISMATCH` (narration tone contradicts band), `DIRECTIVE_IGNORED` (rules directive issued but prose ignores it).

After the table: Does band progression feel too fast, too slow, or appropriate? Was there a coherent momentum arc across the run (low→build→peak or similar)?

### 1A.5 — PacingContext Analysis (Two Signals)

The engine passes two distinct pacing signals: `directive` to the Storyteller (thread/beat decisions), and `outcome_hint` to the Narrator (scene motion). Evaluate each separately.

**Narration → outcome_hint:** For each turn where `pacing_context.outcome_hint` is non-null:
- Was the scene motion honored? ("hold" → continue current pace, "advance" → narrate through to resolution, "transition" → write arrival at new location)

| Turn | PacingContext.outcome_hint | Honored? | Flag |
|------|----------------------------|----------|------|

**Storyteller → directive:** For each turn where `pacing_context.directive` is non-empty:
- Did the storyteller's thread/beat choices align with the directive? (e.g., "Breathe" → no new threads, breathing_room beat; "Pressure"/"Scene Imperative" → tension-building)

| Turn | PacingContext.directive | Thread Action Aligned? | Flag |
|------|-------------------------|------------------------|------|

Flag: `DIRECTIVE_IGNORED_BY_NARRATOR` (outcome_hint not honored), `THREAD_DIRECTIVE_IGNORED` (directive contradicts thread/beat choices).

Evaluate actual directive values: `""`, `"Breathe"`, `"Scene Imperative"`, `"Overwhelm"`, `"Pressure"`, `"Tension"`.

### 1B — GM Beat→Narrative Effect

| Turn Beat Created | Beat Type | Source | Turn Narrated | Beat Reflected in Prose? | Evidence | Flag |
|-------------------|-----------|--------|---------------|--------------------------|----------|------|

The "Source" column distinguishes storyteller-emitted beats from floor-relief-injected breathing_room. Compare `extraction.storytell.output.gm_beat` vs `state_snapshot.meta.pending_gm_beat` — if they differ (storytell emitted null or pressure, state has breathing_room), floor relief fired.

Flag: `NO_EFFECT` (beat present in state but narration unchanged), `WRONG_EFFECT` (beat type=revelation but narration shows complication), `FLOOR_RELIEF_IGNORED` (floor relief injected breathing_room but next turn's narration ignored the recovery tone).

After the table: Are beats creating meaningful story pivots or are they mechanical noise?

### 1B.3 — Surface Flag Consistency

For each unique beat type, list which `surface_as` values appeared:

| Beat Type | surface_as Values | Consistent? | Flag |
|-----------|------------------|-------------|------|

Flag: `SURFACE_DRIFT` (same beat type used different surface_as across turns without a directive change).

surface_as controls how the beat is presented in narration. 'ambient' → background texture, 'environmental' → scene-level pressure, 'npc' → character-focused. Surface drift means the prompt or LLM is inconsistent about how beats are expressed.

### 1B.5 — Beat Generation Quality with Directive Context

For each turn where a beat was generated:
- Was the beat type appropriate given PacingContext.directive? (Note: floor relief can override the beat post-extraction if beat_locked=True — distinguish storyteller-generated beats from floor-relief-injected breathing_room by comparing extraction.storytell.output.gm_beat vs state_snapshot.meta.pending_gm_beat.)

Assessment method:
- **Rule-based**: `""`→none/no beat expected, `"Breathe"`→breathing_room, `"Scene Imperative"`→revelation or escalation (strong scene-level signal), `"Overwhelm"`→complication (short-circuits all other directives when beat_locked fires), `"Pressure"`→complication, `"Tension"`→mild escalation or none.
- **LLM judge**: Let the judge read the beat type + directive and decide if they align. More flexible but subjective.

| Turn Beat Created | Beat Type | PacingContext.directive | Type Matches Directive? | Flag |
|-------------------|-----------|-------------------------|------------------------|------|

Flag: `TYPE_MISMATCH` (beat type contradicts directive).

### 1C — Thread Tension Chain

For each `thread_add` event:

| Thread ID | Added (Tn) | Scope | Consequence Extracted? | Chain Complete? | Flag |
|-----------|------------|-------|------------------------|-----------------|------|

Flag: `INERT_THREAD` (thread exists in state, never feeds into story consequence).

### 1C.5 — Thread Resolution Evaluation

For each resolved thread (in arc.completed_threads[]):
- Was the resolution justified by narration? (narration showed the tension being addressed/resolved)
- For scope=scene threads: was it resolved when the tension ended in the scene?
- For scope=arc threads: was the resolution outcome consistent with the story arc?

| Thread ID | Added (Tn) | Resolved (Tm) | Scope | Narration Justified? | Flag |
|-----------|------------|---------------|-------|---------------------|------|

Flag: `EARLY_RESOLUTION` (resolved before narration showed resolution), `LATE_RESOLUTION` (>3 turns after narrative resolution when the thread was still active), `FALSE_RESOLUTION` (removed when tension was still active in narration), `MISSING_RESOLUTION` (tension resolved narratively but thread not resolved).

### 1C.7 — goal_update → Narrative Effect

For each turn where `storytell.output.goal_update` is non-null:
- Did the visible_goal change produce an observable shift in narration or thread focus in subsequent turns?
- Was the goal_update reflected in the narrator's context (does narration align with the new visible_goal)?

| Turn | goal_update Text | visible_goal After | Narration Shift? | Thread Focus Aligned? | Flag |
|------|------------------|--------------------|-----------------|------------------------|------|

Flag: `GOAL_IGNORED` (goal changed but narration continued as if nothing happened), `GOAL_CONFLICT` (narration contradicts the new visible_goal direction).

### 1D — Condition→Narrative Callback
For each active condition per turn: was it referenced in narration or did it affect a roll directive?

| Condition ID | Active Turns | Referenced in Narration? | Affected Roll? | Flag |
|--------------|--------------|--------------------------|----------------|------|

Flag: `PHANTOM` (in state, never mentioned in prose, never affected anything).

### 1E — Unified Thread→Narrative Chain

For each thread per turn: was the thread's summary or tags reflected in narration? Did thread state changes produce observable story pivots?

| Thread ID | Active Turns | Scope | Referenced in Narration? | State Change? | Flag |
|-----------|--------------|-------|--------------------------|---------------|------|

Flag: `PHANTOM_THREAD` (in arc.threads, never mentioned in prose, never signaled), `STATE_MISMATCH` (thread state changed in state but narration shows no corresponding story event), `SILENT_COMPLETE` (thread marked complete but no narrative resolution).

---

## SECTION 2 — NPC and World Coherence

### 2A — NPC Entry/Exit
Did narration describe NPC entry/exit before or at the same turn the extractor recorded it?
Flag any NPC that left the scene but reappeared without a re-entry narration.
Flag any NPC present in state but never mentioned in narration (ghost NPC).

### 2B — Player Intent Fidelity
For each turn: did the narration process the player's stated action, or redirect/reinterpret it?
Flag turns where the narration output ignores or contradicts the player's stated input.

Verdict: tight / loose / broken.

---

## SECTION 3 — Pacing Assessment

- **High-tension vs breathing turns**: count each. Flag if >4 consecutive high-pressure turns.
- **Momentum arc**: did the run have a discernible arc? Or random oscillation?
- **Beat type variety**: count beat types. Flag if >60% are the same type.
- **recent_beats effectiveness**: the engine tracks last 5 beats in `state.meta.recent_beats` for diversity guidance. Check if beat variety improves over the run (later turns more varied than early turns) — if not, the beat history prompt block may be ineffective.
- **Intent verb variety**: count distinct `intent_verb` values across the run. Flag if >70% are the same verb. Flag if a verb that is known from the scenario (e.g., "negotiate", "sneak", "climb") never appears.
- **Skill coverage**: list which of the 6 skills (`strength, dexterity, wits, lore, charisma, resolve`) appeared in dice rolls. Flag if a skill never appeared across the entire run.
- **Escape paths**: when player was in a bad situation (negative momentum, urgent threads),
  were there viable choices to improve it? Assess from narration content.

---

## SECTION 4 — Scores

### Narrative Score (1–5)
Based on Sections 1–3. Does mechanics produce good fiction? A 5 requires beats, pressures, arc threads, and momentum all producing observable story consequence. A 1–2 means mechanics are decorative.
Score 1–5.

### System Cohesion Score (1–5)
Based on Section 1 chain analyses. Is the engine behaving as a system (mechanics→narrative→state→mechanics) or as isolated components? A 5 requires unified thread lifecycle producing coherent story arcs across turns. Score 1–5.

---

## SECTION 5 — Actionable Issues

Group as **Critical** / **Major** / **Minor**.

- **<description>** (turns: <list>) — Tag: `<tone_mismatch|directive_ignored|inert_mechanic|npc_ghost|intent_redirect|phantom_thread|state_mismatch|silent_complete>`. Fix: <what narrative or mechanic behavior to change>.
