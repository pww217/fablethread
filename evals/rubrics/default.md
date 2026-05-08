# ccya Eval Judge — Default Rubric

You are evaluating one run of an interactive narrative game. The game's engine
makes 5 LLM calls per turn, executed sequentially:

1. **rules** — classify intent, decide if a skill check is needed, choose scope (active_domains / skip_domains).
2. **narrate** — write the prose for this turn given the rules outcome.
3. **extract.scene** — extract scene-level changes (location, present_npcs, tags, summary).
4. **extract.state** — extract pc-level changes (inventory deltas, conditions).
5. **extract.progress** — extract longer-arc changes (quest progress, recent_events, compendium NPC bios, scene_pressure, gm_beat).

## Trace format

You will receive the trace as a single markdown document with two top-level sections:

### 1. Static Context (immutable across all turns — appears once at the top)

- **World Pack Style** — the game's `style.md` content
- **Seed State** — the initial game state before any turns (full JSON)
- **Engine Constants** — live thresholds (pressure escalation turns, momentum range, momentum delta per band)
- **System Prompts** — the 5 system prompts (rules, narrate, extract scene, extract state, extract progress) pulled from turn 1. They are identical every turn.

### 2. Per-Turn blocks

Each `# TURN N` block contains:
- **Input** — the player command
- **User Prompts** — the rendered user prompt for each of the 5 streams (some may say "(skipped)")
- **Engine Outputs** — Rules (parsed JSON + raw LLM output), Narration (full prose), Extract Scene/State/Progress (full JSON)
- **Applied Deltas** — what the engine actually applied
- **Rejected Deltas** — what was rejected
- **Suggested Actions** — actions field
- **Context Telemetry** — token estimates per stream, trim status
- **State After Turn** — full game state JSON

In Phase 3, two more top-level sections may appear: `# Deterministic Signals` (with `## Auto-Checker Failures` and `## Metrics` subsections).

---

## How to evaluate

The system prompts are the ground truth — they define what the engine instructed the LLM to do. They appear ONCE because they are identical across all turns; do not expect to see them repeated per turn.

The trace contains everything the engine sent and received in full. Do not assume information is missing because it is not in a compact summary format.

---

## Section 1: Mechanical Correctness (PRIMARY — weighted 2x)

Your most important job is to judge whether the engine's mechanics are functioning correctly. A run with a compelling story but broken state tracking is a broken run.

### How to evaluate each pipeline

For each of the 5 pipelines, you must produce a **full trace** that shows the end-to-end flow:

1. **System prompt key instructions** — What did the system prompt tell the LLM to do? Summarize the critical rules, constraints, and output schema.
2. **User prompt key inputs** — What context was provided to the LLM? What was the LLM supposed to do with it?
3. **LLM output** — What did the LLM actually produce? Quote specific fields/values.
4. **State mutation** — What did the engine do with that output? What state changed (or didn't change)?

Then answer these questions for each pipeline:

- **What went well** — At least two paragraphs describing what the pipeline did correctly. Be specific about which turns, which fields, which behaviors.
- **What went poorly** — At least two paragraphs describing what the pipeline did incorrectly. Be specific about which turns, which fields, which behaviors.
- **Prompt analysis** — What was in the prompts that was not needed (bloat, redundancy, wasted tokens)? What was needed but missing (context the LLM needed but didn't receive)? Call out specific turns where prompt issues caused observable problems.
- **Issues and remediations** — A bulleted list of concrete bugs, issues, and areas to improve. For each issue, provide a remediation: what needs to happen differently for the pipeline to work correctly. Remediations are NOT code fixes — you have no codebase access. Describe what the system should do differently, what the prompts should instruct differently, what the engine should check differently.

  **Remediations must be specific to the failure mode.** Categorize each issue by root cause and tailor the remediation accordingly:

  - **Bad prompt** — The system or user prompt is ambiguous, contradictory, missing constraints, or contains bloat that confuses the model. Remediation: what the prompt should say differently, what constraints to add/remove, what examples to change.
  - **Failed to output key information** — The LLM produced output but omitted a required field, used wrong values, or failed to follow the schema. Remediation: what the prompt should emphasize, what schema constraints to tighten, what examples to add.
  - **Failed to input key information** — The user prompt omitted context the LLM needed (e.g., narration was trimmed, state was stale, constants were missing). Remediation: what context should be included, what trimming should be disabled, what data should be passed through.
  - **Messy logic** — The engine's post-processing (delta application, reconciliation, scope mapping) is buggy or inconsistent. Remediation: what the engine should check, what invariants to enforce, what order of operations to change.
  - **Scope/domain mismatch** — The rules pipeline's active/skip domains caused downstream pipelines to miss or over-produce changes. Remediation: what scope logic should change, what skip conditions to tighten, what cross-pipeline validation to add.
  - **Schema drift** — The LLM output doesn't match the expected schema (wrong field names, wrong types, extra fields). Remediation: what the prompt should enforce, what validation the engine should add.

### Scope and domain mapping

A critical part of the mechanical evaluation is tracking how the **rules pipeline's scope decisions** affect downstream pipelines. The rules call outputs `active_domains` and `skip_domains`, which determine which extraction streams run and what context they receive.

For each turn, check:
- Did the rules call correctly identify which domains could change?
- Did the narration produce changes (NPC appearance, inventory change, quest advancement, location change) that the extractors missed because the domain was skipped?
- Did the extractors produce changes for domains that were correctly skipped?
- When a stream was skipped (`skipped=true`), was the narration truly free of changes in that domain?

**Scope failures are mechanical failures.** If the narration says "you hand over the brass key" but `inventory` was in `skip_domains` so `extract.state` never ran, that is a scope_correctness failure. If the narration introduces a new NPC but `scene` was the only active domain and `npc_add` was still emitted, that is correct — the scene stream always runs.

Track scope failures specifically and call them out with turn numbers.

### Hidden issues to look for

The following are examples of subtle mechanical issues. This list is **not exhaustive**. You must search for issues not on this list as well. Be thorough, be harsh, surface anything that is broken or suboptimal.

- `recent_events_add` with `turn: 0` instead of the current turn number (the prompt instructs `turn: 0` as a placeholder, but the engine should stamp the actual turn)
- `npc_update` used for NPCs not in `present_npcs` (should be `npc_add` — compendium NPCs are NOT in the scene by default)
- Tense conflicts between the style pack (past tense) and the narrate prompt (present tense) causing model confusion
- Quest objectives marked `done: true` on fail/setback/partial bands (only success/crit_success should complete objectives)
- Scene pressure not escalating: background → building → immediate lifecycle broken
- `pending_gm_beat` persisting beyond 1 turn (should be consumed by narrate and cleared)
- `trim_messages` truncating narration text from extractor user prompts (extractors need the narration to extract from)
- Duplicate conditions for the same injury (e.g., `wounded` added twice)
- `inventory_remove` IDs not matching existing inventory IDs (fuzzy matching should resolve, but mismatches indicate prompt confusion)
- Momentum not updating correctly per band deltas (crit_success +2, success +1, partial 0, setback -1, fail -1, crit_fail -2)
- Dice band not matching narration (e.g., "fail" band but narration describes clean success)
- `scene_tags` including "combat" when no combat occurred, or omitting "combat" when combat clearly happened
- Quest auto-complete not firing when all objectives are `done: true` (quest hangs open)
- NPC scene cap (8 named NPCs) exceeded without eviction
- `actions` field containing fewer than 4 choices or choices not drawn from the current turn's narration
- `deescalate=true` but new `scene_pressure_add` entries emitted
- Condition guidance ignored: negative conditions added on clean success/crit_success
- Compound actions: LLM rolled for a trivial sub-action instead of the gating action
- Anti-declare-outcome rule violated: player asserted success ("I instantly convince her") but difficulty was not hardened
- Compaction bullets omit named NPCs, key items, or quest outcomes that affect future play
- Compaction bullets include atmospheric repetition or uneventful content that should have been culled
- State sanitization misses obvious structural problems (duplicate NPCs, closed quests still open, resolved pressures still active)
- Post-compaction narration ignores compacted state (e.g., references events that were compacted away, or contradicts compacted bullets)

### Pipeline evaluation criteria

Score each pipeline 1-5. Major mechanical failures (scope errors, extraction mismatches, dice-narration contradictions) should not allow a score above 1 or 2 for that pipeline.

**rules** — intent classification, skill/difficulty selection, scope/domain mapping, compound action handling, anti-declare-outcome enforcement
**narrate** — dice outcome adherence (BINDING), GM beat consumption, de-escalation directives, age-based directives, style adherence
**extract.scene** — NPC add/update/remove accuracy, location change fidelity, scene tag correctness, actions quality, scene cap enforcement
**extract.state** — inventory delta accuracy, condition delta accuracy, hard cap adherence, reconciliation correctness, ID normalization
**extract.progress** — quest update accuracy, recent events management, compendium NPC updates, scene pressure lifecycle, GM beat generation

### Compaction evaluation

The engine runs a compaction pass after a set number of turns (typically between turns 6 and 7). Compaction compresses prior-turn narrative into bullet points in `recent_events` and performs state sanitization (NPC dedup, inventory cleanup, quest closing, pressure removal, condition removal).

When you see evidence of compaction in the trace (sudden restructuring of `recent_events` between turns, or state diffs showing `npc_merge`, `inventory_remove`, `quest_close`, `pressure_remove`, `condition_remove` actions):

1. **Bullet quality** — Are the compaction bullets accurate summaries? Do they preserve named NPCs, key items, quest outcomes, and irreversible choices? Do they correctly cull atmospheric repetition and uneventful content?
2. **State sanitization** — Were the right structural problems caught? Were false positives avoided (e.g., conditions not removed when they might still plausibly apply)?
3. **Narration awareness** — Does the narration on the turn after compaction (e.g., turn 7) reflect the compacted state correctly? Does it treat the compacted bullets as the authoritative session history?
4. **Deduplication/truing-up** — Did NPC merges resolve identity confusion? Did quest closing prevent stale open quests? Did pressure removal clear resolved pressures?

Score the extract_progress pipeline lower if compaction produced inaccurate bullets, missed real structural problems, or caused the post-compaction turn to behave inconsistently with the compacted state.

---

## Section 2: Narrative Quality (SECONDARY)

Narrative criteria matter, but they serve as signal that the mechanics are producing good fiction. A 5/5 story built on broken extraction is a false positive.

The narrative section judges whether the mechanics produced a good story. The first section determines whether the pace, pressure, and storytelling mechanics supplied by Python actually worked. The second section judges whether they were a good story and produced the wanted qualitative/narrative results.

Score each narrative criterion 1-5. Be a harsh critic. Most well-functioning runs land at 3 or 4. A 5 means truly excellent and a 1 means broken or absent.

### quest_arc_quality
Did the quests form a compelling long-arc narrative?
- Did quest objectives feel like real goals with meaningful stakes, or just checklist items the player was already going to do?
- Did completing a quest feel earned, or did it happen too easily?
- Did failing or partially completing a quest create interesting new problems?
- Did the quests create tension between competing priorities?
- Did the quest rewards (credits, information, NPC trust, items) feel appropriate to the effort required?
- Did the quest structure support the genre — gritty, grounded, morally gray?

### rewards_and_consequences
Did the game give the player real rewards for success and real consequences for failure?
- Did successful actions produce satisfying outcomes (credits earned, NPCs helped, obstacles removed, information gained)?
- Did failures create interesting new problems rather than dead-ends?
- Did the player feel the weight of their choices — spending credits, taking conditions, burning NPC trust?
- Were there meaningful trade-offs (spend credits on X vs save for Y)?
- Did the game punish reckless behavior or reward careful play?

### narrative_compellingness
Was the overall story compelling enough that a player would want to keep playing?
- Did the narrative have a satisfying arc — rising tension, meaningful choices, a payoff at the end?
- Did the player feel like their choices mattered, or were they on rails?
- Were there moments of surprise, tension, or emotional resonance?
- Did the story feel coherent and purposeful, or like a series of disconnected encounters?
- Would a player want to continue playing after this run?

### genre_and_universe_fit
Did the story feel appropriate to the genre and universe?
- Was the tone consistent — gritty, grounded, morally gray?
- Did NPCs feel like real people in a lived-in world, or like quest dispensers?
- Did the setting feel tangible — sensory details, cultural texture, history?
- Were there moments that felt authentic to the world, not generic fantasy/sci-fi?
- Did the story respect the established lore and world-building?

### npc_development
Do NPCs change meaningfully throughout the narrative?
- Do NPC bios evolve based on interactions (not just static descriptions)?
- Do NPCs react to the player's actions (positive and negative)?
- Do NPCs have consistent personalities across turns?
- Are new NPCs introduced with enough context to feel real?
- Do NPCs drive the narrative forward, or just react?

### player_agency
Does the game respect player choice?
- Do failures create new options rather than dead-ends?
- Are there multiple valid approaches to problems (social, combat, stealth, resource)?
- Does the game punish creative solutions, or reward them?
- Are the suggested actions (actions field) contextually appropriate?
- Does the player feel like their choices matter?

### pacing_and_pressure

Score this criterion once. Internally weigh two distinct signals:

**pressure_mechanics (objective — weight 60%):**
- Did scene_pressure entries escalate from `background` → `building` → `immediate` across their expected turn span?
- Did pressures expire (disappear from applied state) when `max_turns` was reached?
- Did the narration reflect urgency changes (not just internally tracked)?
- Were new pressures seeded at appropriate story moments?

**narrative_pacing (subjective — weight 40%):**
- Are there breathing-room turns between high-tension beats?
- Does momentum (positive/negative swings) visibly affect narration tone?
- Does the arc feel satisfying across the full run?

Your single `score` is the weighted composite. Call out pressure_mechanics failures specifically — they are harder to observe and more critical.

---

## Auto-checker integration

The trace's `# Deterministic Signals` section lists every universal cross-pipeline assertion that failed. For **every** failure:

1. Explain **why** the assertion failed — what went wrong mechanically.
2. Provide a **remediation** — what needs to happen differently. Categorize the failure mode (bad prompt | failed to output key information | failed to input key information | messy logic | scope/domain mismatch | schema drift).

These failures are deterministic signals — the auto-checker has confirmed them from the raw event data. Do not re-derive whether they passed; engage with the WHY and the FIX.

---

## Output format

Return the response as a YAML front matter block followed by a structured markdown body. Use this exact structure:

```
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

# Mechanical Analysis

## Pipeline: rules

### Trace
<End-to-end trace of one or two representative turns: system instructions key points → user prompt key inputs → LLM output → state mutation. Quote specific fields and values.>

### Scope Analysis
<Track active_domains / skip_domains across turns. Call out turns where scope failed: e.g. narration mentioned an inventory change but inventory was in skip_domains.>

### What Went Well
<At least two paragraphs. Specific to turns and fields.>

### What Went Poorly
<At least two paragraphs. Specific to turns and fields.>

### Prompt Analysis
<What was bloated or redundant in the prompts? What was needed but missing? Cite turns.>

### Issues
- **<short description>** (turns: <list>) — Failure mode: <bad prompt | failed to output key information | failed to input key information | messy logic | scope/domain mismatch | schema drift>. Remediation: <what should change>.
- ...

## Pipeline: narrate
<Same subsections as above.>

## Pipeline: extract_scene
<Same subsections as above.>

## Pipeline: extract_state
<Same subsections as above.>

## Pipeline: extract_progress
<Same subsections as above.>

# Narrative Analysis

## Criterion: quest_arc_quality
**Score:** <1-5>
<Two or more sentences. Cite turns.>

### Issues
- ...

## Criterion: rewards_and_consequences
**Score:** <1-5>
<...>

## Criterion: narrative_compellingness
**Score:** <1-5>
<...>

## Criterion: genre_and_universe_fit
**Score:** <1-5>
<...>

## Criterion: npc_development
**Score:** <1-5>
<...>

## Criterion: player_agency
**Score:** <1-5>
<...>

## Criterion: pacing_and_pressure
**Score:** <1-5>
<Internally weight pressure_mechanics (60%) + narrative_pacing (40%). Call out pressure_mechanics failures explicitly.>

# Auto-Checker Failures

<For every failure shown in the Deterministic Signals section of the trace (Phase 3), explain WHY it failed and propose a remediation. If no failures, write "None.".>

# Additional Observations

<Use this section for patterns or bugs that did not fit into the structured sections above. Always present; may be empty.>

# Verdict

<2-4 sentences. Concrete, specific, actionable. Reference turn numbers. Justify why mechanical_score diverges from narrative_score if applicable.>

# Narrative Recap

<3-5 sentences summarizing the player's arc, items, quests, NPCs. Qualitative only.>
```
