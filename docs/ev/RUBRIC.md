# Eval Rubric — How to Check a Game

Use this rubric when inspecting a game session with `ev.py`. Check one area at a time, not all at once. Focused checks produce more accurate findings.

## Priority Order

### 1. Ruling Engine

**What it validates:** Intent classification, band determination, reason quality, dice distribution

**What to look for:**
- `ruling.reason` is non-empty and substantive (not just "ok", "yes", "no", or single word)
- Reason contains causal keywords (because, since, due to, as) or meets minimum word count
- Dice band distribution is not extremely skewed (no single band >80% of rolls)
- `ruling.impossible` flag aligns with player input semantics (LLM check)

**Commands:**
```bash
ev.py check 5 ruling_reason_quality --save-dir saves/my-game
ev.py check 5 ruling_band_distribution --save-dir saves/my-game
ev.py check 5 ruling_intent_match --llm --save-dir saves/my-game
ev.py rolls --save-dir saves/my-game                      # band distribution
ev.py rolls --summary --save-dir saves/my-game            # band summary
```

**Red flags:**
- Reasons are single words or empty
- One dice band dominates (>80% of rolls)
- `impossible` flag contradicts player intent
- Roll band doesn't match dice roll (caught by `roll_band_consistency`)

---

### 2. Phase Engine

**What it validates:** Scene phase transitions, convergence-driven CLIMAX entry, Curtain Call soft-close, breather backstops, thread urgency integration

**What to look for:**
- `scene_phase` transitions follow the state machine: SETUP→RISING→CLIMAX→RESOLUTION/BREATHER
- CLIMAX entry driven by convergence score (≥3 of 5 components), not binary urgency count
- CLIMAX phase respects `climax_turn_limit` (default 4) before transitioning to RESOLUTION
- Curtain Call active on CLIMAX turn 1, forced on `climax_turn_limit - 1`
- BREATHER phase respects `breather_max_turns` (default 3) backstop when no urgent threads appear
- `outcome_hint` is "transition" when CLIMAX hits turn limit
- BREATHER exit condition: `thread_urgency_count > 0` OR `breather_turn_count >= breather_max_turns`

**Commands:**
```bash
ev.py check 5 phase_transition --save-dir saves/my-game
ev.py check 5 pacing_directives --save-dir saves/my-game
ev.py convergence --save-dir saves/my-game
ev.py convergence --by-scene --save-dir saves/my-game     # grouped by scene
ev.py phase-transitions --save-dir saves/my-game
ev.py phase-transitions --by-scene --save-dir saves/my-game
ev.py curtain-call --save-dir saves/my-game
ev.py curtain-call --by-scene --save-dir saves/my-game
```

**Red flags:**
- Phase stuck in CLIMAX beyond turn limit without RESOLUTION transition
- BREATHER soft-locked (no urgent thread, exceeds breather_max_turns)
- Convergence score ≥3 in RISING for 3+ turns without CLIMAX entry
- Curtain Call active/forced but thread_resolve still missing
- `outcome_hint` missing or wrong during CLIMAX resolution

---

### 2. Convergence Score

**What it validates:** The 5-component composite score that drives CLIMAX entry

**What to look for:**
- Score computed fresh each turn from 5 components (urgent_thread, threat_thread, scene_age, beat_streak, dice_weight)
- Each component worth +1; threshold 3 triggers RISING→CLIMAX
- CLIMAX entry always implies at least one urgent thread (score invariant)
- Score 0-2 in RISING should not enter CLIMAX
- `convergence_components` recorded in `pacing_context` on every turn
- Dice weight (+1) only fires when `band in (crit_fail, fail)` AND urgent thread exists
- Beat streak counts pressure-bucket beats (including `setback`) in last 5, uses proportional quorum for <5 entries
- Stored component names match formula (old names `thread_weight`/`urgency_depth` remapped)

**Commands:**
```bash
ev.py convergence --save-dir saves/my-game
ev.py convergence --estimate --save-dir saves/my-game     # retro-compute for saves missing components
ev.py convergence --by-scene --save-dir saves/my-game     # grouped by scene
ev.py phase-transitions --save-dir saves/my-game
ev.py beats --save-dir saves/my-game                      # beat type context
ev.py check 5 beat_phase_validity --save-dir saves/my-game
ev.py check 5 convergence_components --save-dir saves/my-game
```

**Red flags:**
- Score ≥3 in RISING but CLIMAX never fires (phase machine bug)
- Score ≥3 in non-RISING phases irrelevant (score only used for RISING→CLIMAX)
- Components all zero but score >0 (data corruption or pre-convergence save)
- Dice weight fires but no urgent thread active (violates invariant)
- Beat streak includes pending beat (should be history-only)
- Component names don't match formula (old `thread_weight`/`urgency_depth` not remapped)

**What it validates:** The 5-component composite score that drives CLIMAX entry

**What to look for:**
- Score computed fresh each turn from 5 components (urgent_thread, threat_thread, scene_age, beat_streak, dice_weight)
- Each component worth +1; threshold 3 triggers RISING→CLIMAX
- CLIMAX entry always implies at least one urgent thread (score invariant)
- Score 0-2 in RISING should not enter CLIMAX
- `convergence_components` recorded in `pacing_context` on every turn
- Dice weight (+1) only fires when `band in (crit_fail, fail)` AND urgent thread exists
- Beat streak counts pressure-bucket beats (including `setback`) in last 5, uses proportional quorum for <5 entries

**Commands:**
```bash
ev.py convergence --save-dir saves/my-game
ev.py convergence --estimate --save-dir saves/my-game     # retro-compute for saves missing components
ev.py convergence --by-scene --save-dir saves/my-game     # grouped by scene
ev.py phase-transitions --save-dir saves/my-game
ev.py beats --save-dir saves/my-game                      # beat type context
ev.py check 5 beat_phase_validity --save-dir saves/my-game
```

**Red flags:**
- Score ≥3 in RISING but CLIMAX never fires (phase machine bug)
- Score ≥3 in non-RISING phases irrelevant (score only used for RISING→CLIMAX)
- Components all zero but score >0 (data corruption or pre-convergence save)
- Dice weight fires but no urgent thread active (violates invariant)
- Beat streak includes pending beat (should be history-only)

---

### 3. Curtain Call

**What it validates:** Two-tier soft-close mechanism that guides LLM toward thread resolution during CLIMAX

**What to look for:**
- Turn 1 of CLIMAX: `curtain_call: "active"` in storytell prompt, `thread_resolve` required
- Second-to-last turn (`climax_turn_limit - 1`): `curtain_call: "forced"` in both narrate and storytell prompts
- Hard cutoff: engine transitions to RESOLUTION at `climax_turn_limit` regardless
- No `breathing_room` beat in CLIMAX turns 1-2 (only in Scene Imperative override)
- `twist` beat should NOT appear in CLIMAX (removed from Scene Imperative list)

**Commands:**
```bash
ev.py curtain-call --save-dir saves/my-game
ev.py curtain-call --by-scene --save-dir saves/my-game    # grouped by scene
ev.py convergence --save-dir saves/my-game
ev.py beats --save-dir saves/my-game
ev.py check 5 beat_phase_validity --save-dir saves/my-game
```

**Red flags:**
- CLIMAX turn 1 without `thread_resolve` (Curtain Call not guiding LLM)
- Multiple CLIMAX turns without thread_resolve (guidance being ignored)
- `twist` beat in CLIMAX phase (old beat list contaminating prompt)
- `breathing_room` in CLIMAX turn 1-2 (shouldn't be available until Scene Imperative fires)
- Turn at `climax_turn_limit` still in CLIMAX without RESOLUTION transition

---

### 4. GM Beat Lifecycle

**What it validates:** GM beat type transitions, pressure compliance, phase constraints

**What to look for:**
- `pending_gm_beat` from one turn is consumed or updated in the next
- When storyteller emits a GM beat, state's `pending_gm_beat` matches its type
- Beat TTL: storyteller-emitted beats expire after 2 turns (`beat_expires_turn = turn_no + 2`)
- Beat type variety: no more than 2 consecutive same-type beats; at least 1 in 3 beats should be non-pressure
- Beat types respect phase constraints (e.g., no escalation in BREATHER, no breathing_room in CLIMAX unless Scene Imperative)
- Pressure bucket includes: `pressure`, `complication`, `escalation`, `setback`
- `setback` classified as pressure (added in convergence update) — counts toward beat streak

**Commands:**
```bash
ev.py check 5 gm_beat_lifecycle --save-dir saves/my-game
ev.py check 5 beat_phase_validity --save-dir saves/my-game
ev.py beats --save-dir saves/my-game
ev.py trace meta.pending_gm_beat --save-dir saves/my-game
```

**Red flags:**
- Pending beat persists across 3+ turns without consumption
- 3+ consecutive pressure/escalation/complication/setback beats without relief
- Beat types violate phase constraints (e.g., escalation in BREATHER)
- `setback` not counted in pressure streak (should be per convergence update)

---

### 5. Thread Lifecycle & Arc Goals

**What it validates:** Thread add/update correctness, goal alignment, resolution rates

**What to look for:**
- `thread_add` entries appear in next turn's `state_snapshot.arc.threads`
- `thread_update` IDs reference existing threads in `state.arc.threads`
- `goal_update` string from storyteller matches `arc.visible_goal` in state
- Thread progression is meaningful (not tiny increments like 0.50, 0.53, 0.56)
- No orphan threads in state that no sanitizer event ever touches
- Thread resolution rate: threads should resolve within 1-5 turns of creation

**Commands:**
```bash
ev.py check 5 thread_lifecycle arc_goal_updates --save-dir saves/my-game
ev.py threads --save-dir saves/my-game                    # thread state over time
ev.py threads --summary --save-dir saves/my-game          # resolution rate, hallucinated threads
ev.py deltas 7 --save-dir saves/my-game                   # find thread mutations
```

**Red flags:**
- `thread_add` emitted but not in next turn's state
- `thread_update` references non-existent thread ID
- Goal updates don't match visible_goal in state
- Thread progress stuck at tiny increments (LLM dedup rejection pattern)
- Resolution rate below 50% (threads not resolving)
- Hallucinated thread IDs (updated but never created)

---

### 6. Pacing Directives

**What it validates:** outcome hints, directive rendering, beat variety, phase constraints

**What to look for:**
- `outcome_hint` rendered in narrator prompt
- Pacing directive rendered in storyteller prompt
- Removed directives ("location pressure", "location imperative", "combat fatigue", "Overwhelm") not lingering
- Scene Imperative fires at `scene_imperative_threshold` effective turns (default 5)
- Scene Pressure fires at `scene_pressure_threshold` effective turns (default 3)
- Breathe fires when no urgent threads exist AND `breather_turn_count < breather_max_turns`
- Beat type variety: no single type exceeds 70% of all beats (requires 3+ beats)

- Beat types respect phase constraints (allowed_beat_types per phase)

**Commands:**
```bash
ev.py check 5 pacing_directives --save-dir saves/my-game
ev.py check 5 beat_phase_validity --save-dir saves/my-game
ev.py beats --save-dir saves/my-game                      # beat type + effect
ev.py convergence --save-dir saves/my-game                # convergence score context
```

> **Note:** `outcome_hint` is rendered in both `narrate_prompt.rendered_user` and `storytell.rendered_user` (in extraction). The `narrate_prompt` is saved at the event level, not in the `extraction` dict. To verify `pacing_context` rendering, check `storytell.rendered_user` in extraction events or `narrate_prompt.rendered_user` at the event level.

**Red flags:**
- `outcome_hint` missing from narrator prompt
- Single beat type exceeds 70% of total beats
- Removed directives still rendered in prompts
- Beat types violate phase constraints (e.g., escalation in BREATHER)

---

### 7. Inventory & Conditions

**What it validates:** Inventory balance, condition lifecycle, cap enforcement

**What to look for:**
- No negative inventory amounts in `state_snapshot.inventory`
- No overdraw: removing items that don't exist or have zero quantity
- Condition IDs appear in ruling's `reason` text (lowercase comparison)
- No duplicate condition IDs in a single turn
- Condition removals reference conditions that existed in previous turn's state

**Commands:**
```bash
ev.py check 5 inventory_integrity conditions_lifecycle --save-dir saves/my-game
ev.py state --save-dir saves/my-game --format inventory     # current inventory
ev.py state --save-dir saves/my-game --format conditions    # current conditions
ev.py deltas 11 --save-dir saves/my-game                  # find inventory/condition changes
```

**Red flags:**
- Negative inventory amounts
- Removing items not in previous turn's inventory
- More than 5 conditions active simultaneously
- Condition ID in extraction not found in ruling reason text

---

### 9. NPC Presence & Compendium

**What it validates:** NPC lifecycle, compendium consistency, no ghosting

**What to look for:**
- NPCs introduced in scene stay present (no sudden disappearance)
- Valid presence values: `present`, `nearby`, `known`, `departed`
- Departed NPCs have `departed_reason` field
- Compendium updates (`applied.compendium_npc_update`) track NPC state changes correctly
- NPC notes evolve logically across turns

**Commands:**
```bash
ev.py check 5 npc_presence --save-dir saves/my-game
ev.py check 5 compendium_lifecycle --save-dir saves/my-game
ev.py diff 3 10 --section npcs --save-dir saves/my-game   # NPC changes between turns
ev.py deltas 8 --save-dir saves/my-game                   # find NPC mutations
ev.py trace compendium.npcs.<name>.notes --show-unchanged --save-dir saves/my-game
ev.py npc-ghosting --save-dir saves/my-game               # detect NPC ghosting
```

**Red flags:**
- NPC present in turn N, completely missing from compendium in turn N+1 without `compendium_npc_update` entry
- Compendium updates not reflected in next turn's state
- NPC notes regressing or contradicting previous turns
- Departed NPCs missing `departed_reason`

---

### 10. Location & Scene Transitions

**What it validates:** Location continuity, scene tag evolution, no teleporting

**What to look for:**
- When `applied.location_change` is emitted, post-turn location ID differs from previous turn
- Scene tags evolve logically (no sudden scene jumps without transition)
- Environmental shifts tracked in scene state
- Location descriptions match scene context
- Location description is substantive (non-empty, minimum sentences/words)

**Commands:**
```bash
ev.py check 5 location_change --save-dir saves/my-game
ev.py check 5 location_description_consistency --save-dir saves/my-game
ev.py state --save-dir saves/my-game --format location      # current location
ev.py state --save-dir saves/my-game --format scene         # current scene tags
ev.py diff 5 10 --section location --save-dir saves/my-game
```

**Red flags:**
- Location changes without transition narration
- Scene tags jumping between unrelated locations
- `applied.location_change` present but location ID unchanged from previous turn
- Location description empty or too short (<2 sentences, <30 words)

**Known bug (TICK-26):** `applied.location_change` doesn't exist in events — field is `applied.location_description`. Checker returns "required field not found" for every turn.

---

### 10.5. World State Facts

**What it validates:** World state facts are non-empty and substantive

**What to look for:**
- World state facts are non-empty strings (legacy format) or dicts with non-empty `text` field (structured format)
- Facts contain meaningful content (minimum character count)

**Commands:**
```bash
ev.py check 5 world_state_facts --save-dir saves/my-game
ev.py state --save-dir saves/my-game --format scene         # scene/world_state context
```

**Red flags:**
- World state facts empty or too short (<10 chars)
- Structured facts missing `text` field

---

### 11. Sanitizer Lifecycle

**What it validates:** Thread sanitization correctness, no orphan threads, no goal noops

**What to look for:**
- `threads_updated`/`resolved` IDs exist in `state.arc.threads` at the sanitizer's turn (NOT END state — use state snapshots from turn events)
- `threads_added` IDs don't conflict with existing threads at the sanitizer's turn
- No `goal_changed` noops (goal set to same value)
- Orphan threads: threads in state never referenced by any sanitizer event
- Sanitizer events exist in events.jsonl (`kind: "sanitizer"`)

> **Note:** The engine never emits `threads_removed` — it moves threads to `completed_threads[]` instead. The `sanitizer_lifecycle` checker was fixed to not require this field. When checking thread existence, use the state at the sanitizer's turn (from `state_snapshot` in turn events), not the END state, to avoid false positives for resolved threads.

**Commands:**
```bash
ev.py check 5 sanitizer_lifecycle --save-dir saves/my-game
ev.py turn 12 --save-dir saves/my-game                    # full dump, look for sanitizer events
ev.py goals --save-dir saves/my-game                      # goal changes over time (extraction fallback labeled)
```

**Red flags:**
- Sanitizer references thread ID not in state
- Goal changed to same value (noop)
- Threads in state with no sanitizer event ever touching them
- No sanitizer events at all (sanitizer not running)

---

### 12. Warning Signals

**What it validates:** Pipeline warnings — retries, retry errors, rejected items, reconcile warnings

**What to look for:**
- `extract.retries` > 0 indicates extraction pipeline failures
- `retry_errors` per stream (scene, state, storytell) shows which stages failed
- `rejected` list shows items rejected by the pipeline with kind/reason
- `reconcile_warnings` from state reconciliation layer

**Commands:**
```bash
ev.py warnings --save-dir saves/my-game
```

**Red flags:**
- Repeated retries on the same stream (extraction instability)
- High rejected count (pipeline rejecting valid output)
- `reconcile_warnings` accumulating (state sync issues)

**Known gaps (warnings produced but not stored in events):**
- `generate_seed` soft-check → logged only
- Thread update dedup → logged only
- Compendium NPC dedup → modified silently

---

### 13. Prompt Size Analysis

**What it validates:** Token consumption per pipeline stage, growth trends

**What to look for:**
- Token counts grow over time (context accumulation)
- Rate of growth per stage (ruling, narrate, scene extraction, state extraction, storytell)
- Abrupt spikes indicating prompt bloat

**Commands:**
```bash
ev.py prompt-sizes --save-dir saves/my-game
```

**Red flags:**
- Super-linear growth in any stage (prompt bloat)
- Sudden token count jumps between consecutive turns
- Total_in approaching context window limits

---

### 14. LLM-Based Quality Checks (optional, slower)

**What they validate:** Narrative alignment, beat consequences, extraction fidelity, ruling intent

**What to look for:**
- **directive_tone_match:** Narration tone aligns with roll band (success→positive, fail→tense, crit_fail→severe)
- **beat_narrative_chain:** GM beat produces observable narrative consequence in current and next turn narration (pressure→urgency, complication→obstacle, escalation→raised stakes)
- **state_fidelity:** State extraction matches what narration describes — no missing or unsupported changes
- **ruling_intent_match:** Ruling's `impossible` flag matches player input semantics

**Commands:**
```bash
ev.py check 5 directive_tone_match --llm --save-dir saves/my-game
ev.py check 5 beat_narrative_chain --llm --save-dir saves/my-game
ev.py check 5 state_fidelity --llm --save-dir saves/my-game
ev.py check 5 ruling_intent_match --llm --save-dir saves/my-game
```

**Red flags:**
- Success narration reads like a failure (tone mismatch)
- GM beat emitted but no narrative trace of it in subsequent turns
- Narration describes state changes not captured in extraction (or vice versa)
- `impossible` flag contradicts player intent

---

## Validating Items Review

When reviewing an eval group for validating items (bugs in `validating` status awaiting confirmation):

1. **Scan roadmap** — read all `roadmap/bugs/*.md` with `status: validating`
2. **Match to relevant runs** — determine which scenario(s) are relevant to each bug based on bug labels (e.g., `pacing` → convergence issues, `narrative` → beat/story issues)
3. **Run targeted checkers** — check the specific mechanics related to the bug:
   ```bash
   ev.py check 5 <relevant-checker> --save-dir evals/runs/<group>/<run>/
   ```
4. **Confirm or regress:**
   - Bug behavior absent → update status to `done`, set `completed: YYYY-MM-DD`, run `make roadmap`
   - Bug still present → update status to `up-next`, note regression in report
5. **Report** — in consolidated report under "Validating Items":
   - List each validating item with status (confirmed/done or regressed/up-next)
   - Note which run(s) were checked and what checker/command was used

## Git Log Change Assessment

Before running full rubric, assess changes since last eval to focus attention:

```bash
git log --oneline <prior_sha>..<current_sha> -- ccya/
```

**Scope:** Only `ccya/` folder. Ignore `evals/`, `docs/`, `roadmap/`, `plans/`, `scripts/`.

**High-risk areas** (promote to top of rubric review):
- `ccya/prompts/` — extraction, ruling, narrate, storytell prompts
- `ccya/engine/` — pacing, convergence, phase machine
- `ccya/models.py` — state schema changes

Report changes under "Changes Since Last Eval" in the consolidated report.

## Quick Reference — Commands by Goal

| If you want... | Command |
|---|---|
| Phase trajectory | `ev.py trace scene_phase --save-dir saves/my-game` |
| Convergence score + components | `ev.py convergence --save-dir saves/my-game` |
| Convergence score (retro-computed) | `ev.py convergence --estimate --save-dir saves/my-game` |
| Convergence by scene | `ev.py convergence --by-scene --save-dir saves/my-game` |
| Phase transitions with triggers | `ev.py phase-transitions --save-dir saves/my-game` |
| Phase transitions by scene | `ev.py phase-transitions --by-scene --save-dir saves/my-game` |
| Curtain Call compliance | `ev.py curtain-call --save-dir saves/my-game` |
| Curtain Call by scene | `ev.py curtain-call --by-scene --save-dir saves/my-game` |
| Beat type over time | `ev.py beats --save-dir saves/my-game` |
| Roll bands per turn | `ev.py rolls --save-dir saves/my-game` |
| Roll band distribution | `ev.py rolls --summary --save-dir saves/my-game` |
| Thread mutations | `ev.py deltas <N> --save-dir saves/my-game` |
| Thread resolution summary | `ev.py threads --summary --save-dir saves/my-game` |
| NPC changes between turns | `ev.py diff 3 10 --section npcs --save-dir saves/my-game` |
| Inventory snapshot | `ev.py state --save-dir saves/my-game --format inventory` |
| Full mechanics breakdown | `ev.py mechanics 12 --pacing --dice --save-dir saves/my-game` |
| Warning signals | `ev.py warnings --save-dir saves/my-game` |
| Token size analysis | `ev.py prompt-sizes --save-dir saves/my-game` |
| All checkers (summary) | `ev.py check --all --save-dir saves/my-game` |
| All checkers (detailed) | `ev.py check --all --verbose --save-dir saves/my-game` |
| List checkers (no events) | `ev.py check --list` |
| Single checker on single turn | `ev.py check 5 gm_beat_lifecycle --save-dir saves/my-game` |
| Goal changes over time | `ev.py goals --save-dir saves/my-game` |
