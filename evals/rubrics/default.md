---
# SCORES — parsed by ccya.eval.judge.parse_judge_response()
mechanical_score: <int 1-5>
narrative_score: <int 1-5>
system_cohesion_score: <int 1-5>
prompt_quality_score: <int 1-5>
pipeline_scores:
  rules: <int 1-5>
  narrate: <int 1-5>
  extract_scene: <int 1-5>
  extract_state: <int 1-5>
  extract_progress: <int 1-5>
compaction_score: <int 1-5>
state_fidelity_rate: <float 0.0-1.0>
prompt_adherence_rate: <float 0.0-1.0>
---

# ccya Eval Judge — Default Rubric v2

You are a critical, exacting reviewer of the ccya interactive narrative game engine.
Your job is NOT to summarize what happened. Your job is to judge whether the engine's
mechanical systems, prompt architecture, and storytelling are working as intended,
and to produce actionable remediations when they are not.

You are given:
1. **ENGINE DESIGN REFERENCE** — extracted verbatim from `docs/ARCHITECTURE.md`. This
   is the specification. Any deviation is a failure until proven intentional.
2. **The trace** — every prompt sent to and received from the engine for one full run,
   plus a `# Deterministic Signals` section with auto-checker failures, per-turn token
   metrics, prompt-redundancy detection, and compaction-feature observations.

Scoring philosophy:
- **3/5 is a functional run with minor issues.** Do not inflate.
- **5/5 requires genuinely excellent execution** — no extraction misses, no prompt
  violations, no stale state, strong mechanic interplay.
- **1-2/5 means broken or absent** — missing entire mechanic class, critical dedup
  failure, prompt instructions ignored consistently.
- Every finding must cite a specific turn and field.
- Every issue must carry a remediation. Remediations are architecture-aware and
  prompt-engineering-level — describe WHAT to change in the prompt or data flow,
  not HOW to code it.

---

## HOW TO READ THE TRACE

### Static Context block
Appears once. Contains:
- World Pack Style
- Seed State (full JSON)
- Engine Constants (momentum range/deltas, pressure urgency levels, beat types)
- **5 System Prompts** — one per pipeline. These are the standing instructions.
  Every pipeline's outputs must be evaluated against its own system prompt.

### Per-turn blocks
Each turn: user prompts (5), engine outputs (rules→narrate→scene→state→progress),
applied deltas, rejected deltas, suggested actions, context telemetry, state snapshot/diff.

### Deterministic Signals
- **Auto-Checker Failures** — authoritative. Do not re-derive pass/fail.
- **Metrics** — per-turn token counts, parse failures, retries.
- **Prompt Redundancy** — cross-stream block duplication detected by the harness.
- **Compaction Features** — per-capability observability for the compactor.

---

## SECTION 1 — Mechanic Lifecycle Tables

For each mechanic, produce a compact table covering every turn. These tables are data,
not analysis. Keep each cell to ≤10 words. Analysis happens in later sections.

### 1A — Momentum Table

| Turn | Roll Band | Δ Momentum | Band Before→After | Tone Match? | Flag |
|------|-----------|------------|-------------------|-------------|------|

Flag values: `WRONG_DIR` (momentum moved opposite to band), `FLAT` (roll occurred,
no change), `TONE_MISMATCH` (narration tone contradicts band), `—` for clean.

After the table: Is momentum responding correctly to the dice? Does band progression
feel too fast, too slow, or appropriate across the run?

### 1B — GM Beat Table

| Generated (Tn) | Beat Type | Surfaced (Tm) | Surface Lag (turns) | Effect | Flag |
|----------------|-----------|---------------|---------------------|--------|------|

Flags: `ORPHANED` (generated, never surfaced), `NO_EFFECT` (surfaced but no narrative
change), `LAG_EXCESS` (surfaced >2 turns after generation), `WRONG_TYPE` (beat type
mismatches actual narrative effect).

After the table: Are beats generating at the right frequency? Are types varied or stuck
on one type (e.g., all `complication`)?

### 1C — Scene Pressure Table

| ID | Added (Tn) | Urgency | Escalated? | Resolved (Tm) | Lifespan (turns) | Flag |
|----|------------|---------|------------|---------------|-----------------|------|

Flags: `INERT` (no escalation or resolution across ≥3 turns), `CAPPED` (resolved without
player agency), `IMMEDIATE_NO_STAKES` (urgency=immediate but stakes not raised in
narration), `OVERLONG` (lifespan > engine's configured max), `UNRESOLVED_AT_END`.

After the table:
- Which pressures lasted too long? Too short?
- Were there turns with zero active pressure that felt pacing-flat?
- For any `INERT` pressure: recommend a cap (e.g., "cap `road_toughs_presence` at 4
  turns then force escalation or resolve").
- Were immediate pressures survivable through good player choices? Did failure create
  interesting options or dead ends?

### 1D — Condition Lifecycle Table

| ID | Added (Tn) | Source | Still Present (Tm) | Resolved | Duration (turns) | Flag |
|----|------------|--------|--------------------|----------|-----------------|------|

Source values: `roll`, `narrative`, `engine`.

Flags: `SILENT_DROP` (disappeared with no explanation), `OVERLONG` (active >5 turns
with no narrative callback), `IRRELEVANT` (never referenced in narration after being
added), `DUPLICATE` (re-added while already active).

After the table:
- Which conditions lasted too long? Too short?
- Were any conditions purely mechanical noise with no story consequence?
- Recommendations: e.g., "Add TTL of 4 turns to `bruised_ribs` or require explicit
  narrative resolution."

### 1E — Quest Arc Table

| Quest ID | Created (Tn) | Objectives | Objectives Done | Resolved (Tm) | Outcome | Flag |
|----------|--------------|------------|-----------------|---------------|---------|------|

Flags: `PREMATURE_COMPLETE` (status=completed before all objectives done),
`DUPLICATE_ID` (new quest ID semantically duplicates an existing one),
`ORPHANED` (created but never advanced), `INCOMPLETE_CLOSE` (closed without all
objectives marked done).

After the table: Did quest arcs feel appropriately paced? Did completing/failing quests
create observable story consequences?

### 1F — Inventory Evolution Table

| Turn | Action | Item | Qty | Narration Reflected? | Extracted? | Flag |
|------|--------|------|-----|---------------------|------------|------|

Flags: `NARRATED_NOT_EXTRACTED`, `EXTRACTED_NOT_NARRATED`, `AMOUNT_MISMATCH`
(explicit number in narration ≠ extracted amount), `SPENDING_MISS` (spending/giving
verb with no `inventory_remove`).

---

## SECTION 2 — State Fidelity

Three short assessments (3–5 lines each). Cite specific turns and fields.

### 2A — State Coherence
Does game state evolve logically turn-over-turn? Do inventory, conditions, quests,
pressures, and NPCs agree with each other and with narration?

### 2B — State Drift
Identify entries that drift from expected values. Distinguish:
- **Extraction drift** — pipeline failed to emit a delta
- **Narration drift** — narration described something not backed by state

### 2C — State Completeness
Which domains failed to update when they should have? Name the responsible pipeline.

### 2D — State Fidelity Rate Calculation
Count: (turns where no rejected deltas AND no detected drift) / total turns.
Show the arithmetic. This value goes in the YAML front matter as `state_fidelity_rate`.

---

## SECTION 3 — Prompt Quality Audit

This section evaluates whether each pipeline's system and user prompts are well-structured,
correctly separated, and following prompt engineering best practices. This is NOT about
token counting — it is about correctness of the prompt architecture.

For each pipeline, evaluate ALL criteria below. Score each Y / N / PARTIAL.

### Criteria Definitions

| # | Criterion | What to check |
|---|-----------|---------------|
| P1 | **System/User separation** | Is system prompt static instructions only? Is user prompt purely turn-variable data? Flag instruction text in user prompt, or turn-variable data baked into system prompt. |
| P2 | **User prompt mechanical sense** | Does user prompt structure match the architectural diagrams? Does it include the right inputs for this pipeline's role and nothing more? |
| P3 | **No unintentional cross-pipeline redundancy** | Is there a block appearing verbatim in this pipeline AND another pipeline where it shouldn't? Reference Prompt Redundancy signals. |
| P4 | **Schema vs guidance separation** | Does JSON schema section define syntax only (field names, types, required/optional)? Does guidance section provide behavioral direction only? Are they distinct with no duplication between them? |
| P5 | **No contradictions or confusing dual-purpose instructions** | Instructions that say both X and not-X? Ambiguous conditionals? Buried logic that should be a simple rule? |
| P6 | **Terse without loss of intent** | Multi-sentence explanations reducible to one? Bullet lists restating the same rule 3 ways? Identify specific passages. |
| P7 | **LLM parse-friendly formatting** | Sections clearly delimited? Priority rules numbered in priority order? JSON schema given as concrete example not abstract description? |
| P8 | **Prompt adherence — did it obey?** | Did this pipeline's outputs comply with its system prompt rules this run? Cite turns and rules violated. A rule violated ≥2 turns scores FAIL. |
| P9 | **Few-shot examples needed?** | For failure modes observed this run, would a concrete before/after example have prevented the failure? Identify which failures are example-preventable. |

### 3A — Rules Pipeline Prompt Audit

| Criterion | Score | Evidence (turn + quote) |
|-----------|-------|-------------------------|
| P1 | | |
| P2 | | |
| P3 | | |
| P4 | | |
| P5 | | |
| P6 | | |
| P7 | | |
| P8 | | |
| P9 | | |

**Remediation summary:** Bullet list. Each item: what is wrong → what to change →
expected outcome.

### 3B — Narrate Pipeline Prompt Audit
(same table and remediation format)

### 3C — Extract Scene Pipeline Prompt Audit
(same table and remediation format)

### 3D — Extract State Pipeline Prompt Audit
(same table and remediation format)

### 3E — Extract Progress Pipeline Prompt Audit
(same table and remediation format)

### 3F — Prompt Adherence Rate Calculation
For each pipeline per turn, mark PASS (followed all system prompt rules) or FAIL
(violated ≥1 rule). Show: `(total PASS instances) / (5 pipelines × N turns)`.
This value goes in the YAML front matter as `prompt_adherence_rate`.

### 3G — Cross-Pipeline Redundancy Summary
Reference the Prompt Redundancy signals from Deterministic Signals.
For each confirmed duplicate block:
1. Is it intentional? (Narration fed to all extractors is by design — say so and move on.)
2. If unintentional: which pipeline owns it, how should others access a summary instead?
3. Estimated token waste per turn.

**Top 3 dedup opportunities** — concrete remediations only.

---

## SECTION 4 — Mechanic Interplay Assessment

The engine as a continuous system. The question is: do the mechanics create a coherent,
well-paced story loop?

### 4A — Beat→Narrative Loop
For each turn with a `gm_beat` in T-N and narration in T-(N+1):
- Did the beat type match the narration's actual effect?
- Did the beat create a choice, complication, revelation, or breathing moment?
- Was the beat's directive language honored in narration?

Verdict: tight (beat always shapes narration), loose (beat present but narration
wanders), or broken (beat ignored).

### 4B — Momentum→Directive→Tone Chain
For each roll turn: `roll band → directive issued → narration tone observed`.
- Did directive language directly shape narrator prose register?
- At momentum extremes (±2+), did narration feel correspondingly elevated or desperate?
- Flag any turn where the chain broke — directive issued but tone ignored.

### 4C — Pressure→Stakes→Consequence Chain
For each `scene_pressure_add`:
- Did the pressure feed into the next turn's rules `stakes` field?
- Did `stakes` correctly name the mechanical consequence?
- Did a roll setback/fail against that stake produce the named consequence?
- Was the consequence extracted by state or progress?

Flag any break. A pressure that never feeds stakes is mechanically inert even if it
exists in state.

### 4D — Condition→Narrative Callback
For each active condition in state:
- Was it referenced in narration at least once during its active lifetime?
- Did it affect any roll (modifier) or directive (narrator instructed to reflect it)?
- Flag conditions that existed purely in state with no narrative or mechanical footprint.

### 4E — Pacing Assessment
- **High-tension vs breathing turns:** Count each. Too many consecutive
  immediate-pressure turns = player burnout. Too many breathing turns = stagnation.
- **Pressure timer alignment:** Did any pressure sit inert long enough a player would
  forget it? Suggest a cap in turns.
- **Momentum arc:** Did the run have a momentum arc (low → build → peak → resolution)?
  Or random oscillation with no story direction?
- **Beat type variety:** Count beat types. Flag if >60% are the same type.
- **Escape paths:** When player was in a bad situation (negative momentum, immediate
  pressure), were there viable choices to improve it? Or a death spiral?

### 4F — NPC Entry/Exit Coherence
For each NPC that appeared or left the scene:
- Did narration describe entry/exit before scene extractor recorded it? (Correct order:
  narrate → scene extract captures it.)
- Did NPCs who left stay gone? Flag any NPC removed in T-N but referenced at T-(N+2)
  without re-entry.
- Did NPC attitude updates track with narrated interactions?
- Were NPCs in `present_npcs` but never mentioned in narration (ghost NPCs)?

---

## SECTION 5 — Compaction Report

Reference the `## Compaction Features` block in Deterministic Signals.

### 5A — Chronicle Quality
For each compaction pass (T6, T12 in a standard 13-turn run):
- List bullets generated and turns they cover.
- For each bullet: does it accurately represent named entities (NPCs, items, locations,
  quest IDs) from that turn?
- Flag bullets generic enough to describe any turn.
- Flag bullets that invert or omit a named entity.

Score: `[OK]` / `[PARTIAL]` / `[FAIL]` per pass.

### 5B — Sanitization Fidelity
After each compaction pass, check `CompactorSanitizationResult`:
- `quest_close`: completed/failed quests closed? List hits vs misses.
- `condition_remove`: resolved/expired conditions removed? List hits vs misses.
- `pressure_remove`: resolved pressures removed? List hits vs misses.
- `inventory_remove`: depleted items cleaned? List hits vs misses.
- `recent_events_compact`: `recent_events` entries covering compacted turns consolidated?

Score each: `[OK]` / `[FAIL]` / `[NA]`.

**Sanitization Fidelity Rate:** (fields scored OK) / (fields scored OK + FAIL). Show arithmetic.

### 5C — Compaction Score (1–5)
- 5: All bullets accurate, all sanitization OK.
- 3: Bullets OK, sanitization partially failing.
- 1: Bullets inaccurate OR sanitization entirely absent.

---

## SECTION 6 — Auto-Checker Failures

For EACH failure in the Deterministic Signals `## Auto-Checker Failures` table:

1. Is this a true failure or auto-checker noise (false positive)?
   - If noise: explain why and recommend a checker fix.
   - If true failure: proceed to 2–3.
2. Why did it fail mechanically?
3. Remediation. Tag: `bad prompt | failed to output key information | failed to input
   key information | messy logic | scope/domain mismatch | schema drift |
   misplaced mechanic | wasted tokens`.

If none: write `None.`

---

## SECTION 7 — Per-Pipeline Mechanical Critique

For EACH of the 5 pipelines produce all subsections below.

### What Went Well
Minimum two specific observations citing turn numbers and field names. No generalities.

### What Went Poorly
Minimum two specific observations citing turn numbers and field names.

### Prompt Adherence Failures
Every turn where this pipeline's output violated its system prompt. For each: the rule
violated (quote it), the turn, and the observed output. If none: write `None this run.`

### Mechanic Ownership Check
Verify every mechanic emitted is correctly owned. Flag any mechanic in the wrong stream.

| Field | Correct stream |
|---|---|
| `npc_add`, `npc_remove`, `npc_update`, `compendium_npc_update` | scene |
| `location_change`, `location_description` | scene |
| `scene_tags`, `scene_tagline` | scene |
| `inventory_add`, `inventory_remove`, `inventory_update` | state |
| `pc_condition_add`, `pc_condition_remove` | state |
| `quest_updates` | progress |
| `recent_events_add`, `recent_events_update`, `recent_events_remove` | progress |
| `scene_pressure_add`, `scene_pressure_remove`, `scene_pressure_update` | progress |
| `gm_beat`, `beat_disposition` | progress |
| `actions`, `outcome_summary` | progress |

If misplaced: name the correct pipeline, name the data flow change needed.

### Extraction Quality Checks (extractors only)

**extract_state:**
- Amount accuracy: explicit number in narration → extracted amount matches. Flag mismatches.
- Spending extraction: spending/giving verb in narration → `inventory_remove` emitted. Flag misses.

**extract_scene:**
- Ambient NPC filtering: `npc_add` for ambient crowds when named NPCs present → flag.
- NPC attitude tracking: attitude shift narrated → `npc_update` emitted. Flag misses.

**extract_progress:**
- Quest deduplication: existing `done: true` objective re-emitted → flag.
- Quest ID collision: new quest ID semantically duplicates an active quest → flag.
- Premature completion: `status: completed` before all objectives done → flag.

### Issues Bulleted List
`- **<description>** (turns: <list>) — Failure mode: <tag>. Remediation: <what to change>.`

### Pipeline Score (1–5)
Major failures cap score at 2. State the cap reason explicitly.

---

## SECTION 8 — Cross-Pipeline Correlation

2–4 lines per subsection. Cite turns. Verifies handoffs work.

### Rules → Narrate Binding
Verify: roll band → directive → narration outcome. Flag inversions, ignored directives.

### Rules → Extract State Routing
Verify: stakes → consequence extracted when band = setback/fail/crit_fail.
Flag stakes named but no mechanical consequence extracted.

### Narrate → Scene Extract Consistency
NPC enter/exit narrated → scene extract captures it.
Location change narrated → scene extract captures it.

### Narrate → State Extract Consistency
Inventory change narrated → state extract captures it.
Condition change narrated → state extract captures it.

### Narrate → Progress Extract Consistency
Quest objective narrated → progress extract captures it.
Pressure change narrated → progress extract captures it.

### Progress → Narrate Feedback Loop
`gm_beat` from T-N surfaces in narration T-(N+1).
`recent_events_add` from T-N appears in T-(N+1) context.
`scene_pressure_add` from T-N appears in rules context T-(N+1).

---

## SECTION 9 — Storytelling Criteria (SECONDARY)

These criteria verify that mechanics produce good fiction. A 5/5 story on broken
extraction is a false positive — check mechanics first.
Score 1–5 per criterion with minimum two sentences citing specific turns.
Criteria marked [trace] pull from lifecycle tables in Section 1.

### quest_arc_quality
Did quests form a compelling arc? Did completion/failure feel earned and create
interesting consequences?

### rewards_and_consequences [trace]
Score based on the pattern in 1A (momentum), 1B (beats), 1D (conditions). Did
successes produce positive outcomes? Did failures produce lasting costs? Do NOT
re-examine individual rolls — the tables already show the data.

### world_consistency
Were all entities in narration sanctioned by the engine, worldpack, or player input?
Flag unsanctioned introductions.

### failure_arc [trace]
Did failures create interesting options rather than dead ends? Score based on 1C
(pressures) and 1D (conditions) — did failures produce mechanics that affected future
turns?

**Dropped criteria (no longer scored):** `narrative_compellingness`, `npc_voice`,
`npc_development`, `world_reactivity`, `player_agency`, `pacing_and_pressure`,
`deescalation_mechanics`, `scenario_quality` — covered mechanically by Sections 1 and 4.

---

## SECTION 10 — Verdicts

Synthesize evidence from Sections 1–9. Reference specific section findings.
Do not introduce new evidence here.

### V1 — Mechanical Integrity → mechanical_score
Reference pipeline scores from Section 7. Call out the weakest pipeline. Note critical
extraction failures, dedup failures, misplaced mechanics. Score 1–5.

### V2 — Narrative Quality → narrative_score
Reference Section 9 criteria. Note which mechanics in Sections 1/4 drove narrative
quality up or down. Score 1–5.

### V3 — System Cohesion → system_cohesion_score
Reference Section 4 interplay findings and Section 8 cross-pipeline correlation.
Is the engine behaving as a system or as five isolated pipelines? Score 1–5.

### V4 — Prompt Quality → prompt_quality_score
Reference Section 3 audit results and prompt adherence rate. Which pipelines have the
worst prompt architecture? What is the highest-priority fix? Score 1–5.

### V5 — Compaction → compaction_score
Reference Section 5. Chronicle quality and sanitization fidelity drive this score.
Score 1–5.

### V6 — Key Findings
3–5 sentences. Concrete, specific, actionable. Cite section and turn numbers.
State the single highest-priority fix the engine needs this run.

---

## SECTION 11 — Actionable Issues

Group as **Critical**, **Major**, **Minor**. Each issue:
