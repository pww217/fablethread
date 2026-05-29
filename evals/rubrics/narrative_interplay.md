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
- **Extraction outputs**: scene (NPCs, location), state (inventory, conditions), progress (unified threads, beats)
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

### 1A.5 — PacingContext.directive Analysis

For each turn where pacing_context.directive is non-empty:
- Was the directive honored in narration? (e.g., "Breathe" → low-urgency prose, "Pressure"/"Overwhelm" → tension-building)

| Turn | PacingContext.directive | Honored? | Flag |
|------|-------------------------|----------|------|

Flag: `DIRECTIVE_IGNORED_BY_NARRATOR`.

Evaluate actual directive values: `""`, `"Breathe"`, `"Scene Imperative"`, `"Overwhelm"`, `"Resolve a Threat"`, `"Pressure"`, `"Tension"`, `"Threat Pressure"`, `"Scene Pressure"`.

### 1B — GM Beat→Narrative Effect

| Turn Beat Created | Beat Type | Turn Narrated | Beat Reflected in Prose? | Evidence | Flag |
|-------------------|-----------|---------------|--------------------------|----------|------|

Flag: `NO_EFFECT` (beat present in state but narration unchanged), `WRONG_EFFECT` (beat type=revelation but narration shows complication).

After the table: Are beats creating meaningful story pivots or are they mechanical noise?

### 1B.3 — Surface Flag Consistency

For each unique beat type, list which `surface_as` values appeared:

| Beat Type | surface_as Values | Consistent? | Flag |
|-----------|------------------|-------------|------|

Flag: `SURFACE_DRIFT` (same beat type used different surface_as across turns without a directive change).

surface_as controls how the beat is presented in narration. 'ambient' → background texture, 'environmental' → scene-level pressure, 'npc' → character-focused. Surface drift means the prompt or LLM is inconsistent about how beats are expressed.

### 1B.5 — Beat Generation Quality with Directive Context

For each turn where a beat was generated:
- Was the beat type appropriate given PacingContext.directive? (e.g., "Breathe" → breathing_room, "Pressure"/"Overwhelm" → complication)

Assessment method:
- **Rule-based**: `""`→none/no beat expected, `"Breathe"`→breathing_room, `"Scene Imperative"`→revelation or escalation (strong scene-level signal), `"Overwhelm"`→complication (more severe than Pressure, short-circuits all other directives), `"Resolve a Threat"`→resolution guidance for aged-out threats, `"Pressure"`/`"Threat Pressure"`→complication, `"Tension"`→mild escalation or none, `"Scene Pressure"`→mild scene-level pressure.
- **LLM judge**: Let the judge read the beat type + directive and decide if they align. More flexible but subjective.

| Turn Beat Created | Beat Type | PacingContext.directive | Type Matches Directive? | Flag |
|-------------------|-----------|-------------------------|------------------------|------|

Flag: `TYPE_MISMATCH` (beat type contradicts directive).

### 1C — Thread Tension Chain

For each `thread_add` event:

| Thread ID | Added (Tn) | Scope | Consequence Extracted? | Chain Complete? | Flag |
|-----------|------------|-------|------------------------|-----------------|------|

Flag: `INERT_THREAD` (thread exists in state, never feeds into story consequence).

### 1C.5 — Thread Expiration Evaluation

For each resolved/expired thread:
- Was the expiration justified by narration? (narration showed the tension being addressed/resolved)
- For scope=scene threads: was it expired on location change per engine rules?
- For scope=arc threads: was age-based demotion applied correctly via last_seen_turn?

| Thread ID | Added (Tn) | Resolved/TTL (Tm) | Scope | Location Changed? | Narration Justified? | Flag |
|-----------|------------|-------------------|-------|-------------------|---------------------|------|

Flag: `EARLY_EXPIRATION` (expired before narration showed resolution), `LATE_EXPIRATION` (>3 turns after location change when narration showed resolution for scope=scene, or >8 idle turns for scope=arc), `FALSE_EXPIRATION` (removed when tension was still active in narration), `MISSING_EXPIRATION` (tension resolved but thread not expired).

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
