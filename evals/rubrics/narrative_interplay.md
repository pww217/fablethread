***
narrative_score: <int 1-5>
system_cohesion_score: <int 1-5>
***

# ccya Eval — Narrative & Mechanic Interplay Judge

You are evaluating whether the ccya engine's narrative output correctly reflects
and responds to its mechanical state. You are NOT auditing prompt architecture
or extraction schema correctness — those are handled by other judges.

Your trace contains:
- Narration text per turn (the actual prose shown to players)
- Rules output: roll band, directive, stakes, intent per turn
- Mechanic state fields per turn: momentum, GM beats, scene pressures, conditions, arc threads, NPCs
- State diffs (mechanic-relevant fields only)

Every finding must cite a specific turn and field.

Scoring philosophy:
- 5/5: Narration consistently honors directives, tone matches momentum, every beat/pressure
  creates observable story consequence.
- 3/5: Minor disconnects (1–2 turns), no systematic failures.
- 1–2/5: Directives routinely ignored, tone disconnected from momentum band, mechanics
  create no story consequence.

***

## HOW TO READ YOUR TRACE

Per-turn blocks contain:
- **Rules output**: `band`, `directive`, `stakes`, `intent`, `roll` (if present)
- **Narration**: the prose output
- **Extraction outputs**: scene (NPCs, location), state (inventory, conditions), progress (arc threads, pressures, beats)
- **State diff**: changes to `meta.momentum`, `scene`, `pc.conditions`

You do NOT have access to the system or user prompts — do not comment on prompt architecture.

***

## SECTION 1 — Mechanic→Narrative Chain Analysis

### 1A — Rules Directive + Narration Directive → Tone

For each turn with a roll:

| Turn | Band | Rules Directive | Narration Directive | Tone Match? | Evidence (quote ≤15 words) | Flag |
|------|------|-----------------|---------------------|-------------|---------------------------|------|

Flag: `TONE_MISMATCH` (narration tone contradicts band), `DIRECTIVE_IGNORED` (rules directive issued but prose ignores it), `NARRATION_DIRECTIVE_IGNORED` (narration_directive present but prose contradicts it).

After the table: Does band progression feel too fast, too slow, or appropriate? Was there a coherent momentum arc across the run (low→build→peak or similar)?

### 1A.5 — Narration Directive Analysis

For each turn where narration_directive is non-empty:
- Was the directive honored in narration? (e.g., Breathe → low-urgency prose, Overwhelm → chaotic/overlapping events)
- Was the directive available to the progress extractor? (Check if it appears in extract_progress_user prompt)
- Did the progress extractor use it for beats/pressure decisions?

| Turn | Narration Directive | Honored? | Available to Extractor? | Used for Beat/Pressure? | Flag |
|------|---------------------|----------|------------------------|------------------------|------|

Flag: `DIRECTIVE_NOT_RENDERED` (computed but not in narrate prompt), `DIRECTIVE_IGNORED_BY_NARRATOR`, `DIRECTIVE_NOT_IN_PROGRESS_PROMPT`, `DIRECTIVE_AVAILABLE_BUT_UNUSED`.

Evaluate all 9 directive types: Breathe, Pressure, Overwhelm, Tension, Combat Fatigue, Location Imperative, Location Pressure, Threat Pressure, Resolve a Threat.

### 1B — GM Beat→Narrative Effect

| Turn Beat Created | Beat Type | Turn Narrated | Beat Reflected in Prose? | Evidence | Flag |
|-------------------|-----------|---------------|--------------------------|----------|------|

Flag: `NO_EFFECT` (beat present in state but narration unchanged), `WRONG_EFFECT` (beat type=revelation but narration shows complication).

After the table: Are beats creating meaningful story pivots or are they mechanical noise?

### 1B.5 — Beat Generation Quality with Directive Context

For each turn where a beat was generated:
- Was the beat type appropriate given the narration_directive? (e.g., Breathe → breathing_room beat, Pressure → complication beat)
- Was the beat generation informed by the directive context available in the progress prompt?

Assessment method:
- **Rule-based**: Breathe→breathing_room, Pressure/Overwhelm→complication, Tension→complication or revelation, Combat Fatigue→complication, Location Imperative→complication, Location Pressure→complication, Threat Pressure→complication, Resolve a Threat→revelation or complication.
- **LLM judge**: Let the judge read the beat type + directive and decide if they align. More flexible but subjective.

| Turn Beat Created | Beat Type | Narration Directive | Type Matches Directive? | Flag |
|-------------------|-----------|---------------------|------------------------|------|

Flag: `TYPE_MISMATCH` (beat type contradicts directive), `DIRECTIVE_INFORMED` (beat type aligns with directive).

### 1C — Pressure→Stakes→Consequence Chain

For each `scene_pressure_add` event:

| Pressure ID | Added (Tn) | Stakes Named? | Consequence Extracted? | Chain Complete? | Flag |
|-------------|------------|---------------|------------------------|-----------------|------|

Flag: `INERT_PRESSURE` (pressure exists in state, never feeds stakes), `STAKES_WITHOUT_CONSEQUENCE` (stakes named, roll setback, no consequence extracted).

### 1C.5 — Pressure Removal Evaluation

For each `scene_pressure_remove` event:
- Was the removal justified by narration? (narration showed the threat being addressed/resolved)
- Was the removal timely? (removed within 2-3 turns of narration showing resolution — pacing should not lock a player into a threat for more than a few turns)
- Was the removal correct? (no false removals — pressure removed when it shouldn't have been)

| Pressure ID | Added (Tn) | Resolved (Tm) | Turns to Remove | Narration Justified? | Correct? | Flag |
|-------------|------------|---------------|-----------------|---------------------|----------|------|

Flag: `EARLY_REMOVAL` (removed before narration showed resolution), `LATE_REMOVAL` (persisted >3 turns after narration showed resolution), `FALSE_REMOVAL` (removed when threat was still active), `MISSING_REMOVAL` (threat resolved in narration but pressure not removed).

### 1D — Condition→Narrative Callback

For each active condition per turn: was it referenced in narration or did it affect a roll directive?

| Condition ID | Active Turns | Referenced in Narration? | Affected Roll? | Flag |
|--------------|--------------|--------------------------|----------------|------|

Flag: `PHANTOM` (in state, never mentioned in prose, never affected anything).

### 1E — Arc Thread→Narrative Chain

For each active thread per turn: was the thread's summary or tags reflected in narration? Did thread state changes (latent→active, active→complete) produce observable story pivots?

| Thread ID | Active Turns | Thread State | Referenced in Narration? | State Change? | Flag |
|-----------|--------------|--------------|--------------------------|---------------|------|

Flag: `PHANTOM_THREAD` (in active_threads, never mentioned in prose, never signaled), `STATE_MISMATCH` (thread state changed in state but narration shows no corresponding story event), `SILENT_COMPLETE` (thread marked complete but no narrative resolution).

***

## SECTION 2 — NPC and World Coherence

### 2A — NPC Entry/Exit
Did narration describe NPC entry/exit before or at the same turn the extractor recorded it?
Flag any NPC that left the scene but reappeared without a re-entry narration.
Flag any NPC present in state but never mentioned in narration (ghost NPC).

### 2B — Player Intent Fidelity
For each turn: did the narration process the player's stated action, or redirect/reinterpret it?
Flag turns where the narration output ignores or contradicts the player's stated input.

Verdict: tight / loose / broken.

***

## SECTION 3 — Pacing Assessment

- **High-tension vs breathing turns**: count each. Flag if >4 consecutive immediate-pressure turns.
- **Momentum arc**: did the run have a discernible arc? Or random oscillation?
- **Beat type variety**: count beat types. Flag if >60% are the same type.
- **Escape paths**: when player was in a bad situation (negative momentum, immediate pressure),
  were there viable choices to improve it? Assess from narration content.

***

## SECTION 4 — Scores

### Narrative Score (1–5)
Based on Sections 1–3. Does mechanics produce good fiction? A 5 requires beats, pressures, arc threads, and momentum all producing observable story consequence. A 1–2 means mechanics are decorative.
Score 1–5.

### System Cohesion Score (1–5)
Based on Section 1 chain analyses. Is the engine behaving as a system (mechanics→narrative→state→mechanics) or as isolated components? A 5 requires arc thread lifecycle (latent→active→complete) producing coherent story arcs across turns. Score 1–5.

***

## SECTION 5 — Actionable Issues

Group as **Critical** / **Major** / **Minor**.

- **<description>** (turns: <list>) — Tag: `<tone_mismatch|directive_ignored|inert_mechanic|npc_ghost|intent_redirect|phantom_thread|state_mismatch|silent_complete>`. Fix: <what narrative or mechanic behavior to change>.
