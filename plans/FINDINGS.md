# ARC System Findings

**Date:** 2026-05-16
**Scope:** ARC system behavior across 6 turns of default save
**Method:** `scripts/debug/get-mechanics.sh` + `get-deltas.sh` per turn, direct state.yaml inspection

---

## What's Working

### Thread creation from `candidate_opportunity`
Working correctly. 4 latent threads were created from opportunities across turns 1-5:

| Thread | Created T# | Summary |
|--------|-----------|---------|
| `the_flickering_grid` | 1 | Power grid failing, scavengers might stabilize it |
| `the_metallic_wreckage_wedged_between` | 1 (latent) / 3 (active) | Wreckage may contain circuitry for repairs |
| `the_valuable_find_could_attract` | 3 | Noise could attract scavengers/hostiles |
| `joe_salazar_might_offer_a` | 4 | Joe might offer bigger contract |
| `the_fedra_connection` | 1 (latent, never promoted) | Leadership secret deals with FEDRA |

### Thread progression via `thread_signals`
Working. Threads increment progress when the progress extractor signals `advanced`:

| Turn | Thread | Signal | Result |
|------|--------|--------|--------|
| 1 | `the_flickering_grid` | advanced | 0→1 |
| 3 | `the_metallic_wreckage_wedged_between` | advanced | 0→1 |
| 4 | `the_metallic_wreckage_wedged_between` | advanced | 1→2 |
| 5 | 2 threads signaled | advanced | 1 increment (dedup) |
| 6 | `joe_salazar_might_offer_a` | advanced | 0→1 |

### Latent thread promotion
Working. `the_flickering_grid` was promoted from latent→active at T1 (no `unlock_if` guard), then failed at T2.

`the_fedra_connection` correctly stays latent — has `unlock_if: "Player investigates settlement leadership records"`.

### Drift analysis scoring
Working. Values increment consistently (1→2→3) showing engagement tracking.

### Campaign Arc section in narrate prompt
Rendering correctly with goal, phase, PC drive, active threads with urgency/progress, discovered truths.

### State persistence
Arc state survives compaction. `meta.last_compacted_turn = 4` and arc data is intact through T6.

---

## Issues

### 1. `the_metallic_wreckage_wedged_between` stuck at 2/3 since T4

**Problem:** The thread summary says "The metallic wreckage wedged between the transit hub pillars may contain the specific circuitry needed for repairs." This objective was materially resolved at T3 (components found) and T4 (components installed). But the thread only has 2 increments.

**Root cause:** The progress extractor didn't emit a thread signal at T4. The extractor saw the installation as a "success" of the overall arc goal but didn't recognize it as a distinct engagement with the thread. The thread summary became stale — it still references "wreckage may contain circuitry" even though those components were found and installed.

**Impact:** The main arc thread is stalled. It needs one more `advanced` signal to reach 3/3 and complete.

### 2. `the_valuable_find_could_attract` still at 0/3 since T3

**Problem:** Created from the T3 opportunity. No signals have ever touched it.

**Assessment:** This is reasonable pacing. The thread is about "scavengers attracted by noise." The player hasn't had any gameplay moment that engages with this risk. It's a background tension thread that hasn't been triggered yet.

### 3. `joe_salazar_might_offer_a` progressing slowly

**Problem:** Created at T4, progressed at T6 (0→1).

**Assessment:** This is a "tactical/background" thread. Slow progression is expected. It's a 3/3 thread that's only 1/3 after 6 turns.

### 4. No thread has reached progress 3

**Problem:** The completion threshold (`_THREAD_COMPLETION_THRESHOLD = 3`) hasn't been hit in 6 turns.

**Assessment:** Could be by design (slow pacing) or could indicate the system needs more frequent engagement signals. With 4 active threads competing for attention, 6 turns may simply not be enough.

### 5. Thread summary doesn't evolve

**Problem:** `the_metallic_wreckage_wedged_between` still says "wreckage may contain circuitry" at T6 even though those components were found at T3 and installed at T4.

**Impact:** The narrate prompt shows stale thread summaries, which could confuse the LLM's understanding of what the thread is actually about.

---

## Thread Lifecycle Through 6 Turns

```
T1:  the_flickering_grid          latent → active → progress 1
     the_metallic_wreckage...      latent (unlock_if present, not promoted)
     the_fedra_connection          latent (unlock_if present, not promoted)

T2:  the_flickering_grid          progress 1 (no increment — player didn't engage)

T3:  the_flickering_grid          still 1 (thread eventually fails)
     the_metallic_wreckage...      latent → active → progress 1
     the_valuable_find...          latent created from candidate_opportunity

T4:  the_flickering_grid          fails (moved to completed_threads)
     the_metallic_wreckage...      progress 1→2
     the_valuable_find...          still 0
     joe_salazar...                latent created from candidate_opportunity

T5:  the_metallic_wreckage...      still 2 (dedup: 2 signals = 1 increment)
     the_valuable_find...          still 0
     joe_salazar...                still 0
     new pressure: secondary_grid_failure

T6:  the_metallic_wreckage...      still 2 ← STUCK
     the_valuable_find...          still 0
     joe_salazar...                0→1
     new pressure: secondary_grid_failure (building)
```

---

## State Data

### Current arc state (from state.yaml at T6)

```yaml
arc:
  phase: setup
  visible_goal: Secure functional electrical components for the settlement filtration system.
  thematic_question: What is the cost of maintaining a dying civilization?
  pc_drive: Providing reliable power to keep his community from thirsting.
  arc_engagement: 2
  active_threads: 4
  completed_threads: 1 (the_flickering_grid — failed)
  latent_threads: 1 (the_fedra_connection — has unlock_if)
  discovered_truths: []
  hidden_truths: 2
```

### Key constants

| Constant | Value |
|----------|-------|
| `_THREAD_COMPLETION_THRESHOLD` | 3 |
| `_ACTIVE_THREAD_CAP` | 4 |
| `_LATENT_CAP` | 4 |

### Thread signal types

| Signal | Effect |
|--------|--------|
| `advanced` | Increments progress by 1 |
| `blocked` | No effect on progress |
| `failed` | Moves to completed_threads with state="failed" |
| `ignored` | No effect |

---

## Progress Extractor Analysis

### What the extractor received (inputs)

The progress extractor's user prompt contained these sections each turn:

| Section | Present T1-T6? | Source |
|---------|---------------|--------|
| `## characters` | Yes | Scene stream — NPC roster with presence status |
| `## location` | Yes | Scene stream — current location description |
| `## active_threads` | Yes | State — arc.active_threads with summary + tags |
| `## recent_events` | Yes | State — scene.recent_events |
| `## Current inventory` | Yes | State stream — current inventory |
| `## last_turn_narration` | Yes T2-T6 | Previous turn's narration |
| `## player_intent` | Yes | Rules stream — intent + verb + stakes + check |
| `## CURRENT TURN NARRATION` | Yes | Narrate stream — rendered narration |
| `## rules_stakes` | Yes T2-T6 | Rules band + at-risk cost |
| `## gm_beat` | Yes T1-T6 | Pending/active GM beat |
| `## pending_beat` | Yes T4-T6 | Carried beat from previous turn |
| `## deescalation` | Yes T6 | Narrative velocity |
| `## narration_directive` | Yes T6 | Tone directive |
| `## Current Pressures` | Yes T5-T6 | Scene pressures |

**Assessment:** The extractor had comprehensive, well-structured input. All relevant game state was present.

### What the extractor produced (outputs)

| Turn | thread_signals | candidate_opportunity | recent_events_add | scene_pressure_add | gm_beat | outcome_summary |
|------|---------------|----------------------|-------------------|-------------------|---------|----------------|
| 1 | `the_flickering_grid` → advanced | "metallic wreckage may contain circuitry" | substation_vine_overgrowth | — | — | "You and Richard White arrive at the overgrown transit hub..." |
| 2 | `the_flickering_grid` → failed | — | — | — | — | "Your search... proves fruitless..." |
| 3 | `the_metallic_wreckage_wedged_between` → advanced | "valuable find could attract scavengers" | junction_box_salvage | — | opportunity (Richard White reckless) | "You successfully locate a shielded junction box..." |
| 4 | `the_metallic_wreckage_wedged_between` → advanced | "Joe Salazar might offer a contract" | filtration_system_stabilized | — | opportunity (Joe Salazar offers respite) | "You successfully integrated the salvaged components..." |
| 5 | `the_metallic_wreckage` → ignored, `the_valuable_find` → ignored | "failing cooling pumps present new opportunity" | secondary_grid_instability | secondary_grid_failure (building) | complication (infirmary lights) | "You demonstrate tech to Joe... new crisis in secondary grid" |
| 6 | `joe_salazar_might_offer_a` → advanced | — | voltage_stabilization_success | — | complication (cooling pumps struggling) | "You stabilized voltage... surge has migrated elsewhere" |

### Turn-by-turn assessment

#### Turn 1 — GOOD
- **Decision:** Advanced the_flickering_grid, created "metallic wreckage" opportunity
- **Assessment:** Correct. The player was actively searching for electrical components, directly engaging the grid thread. The new opportunity about wreckage was a smart addition — it gave the system a second thread to work with.
- **Inputs used:** active_threads (1 thread), player_intent (search), narration (mentions metallic wreckage)

#### Turn 2 — GOOD
- **Decision:** Failed the_flickering_grid, no new opportunity
- **Assessment:** Correct. The search found nothing but slag. The band was FAIL. The extractor correctly recognized this as a thread failure, not an advancement. The narration explicitly says "nothing but grit and rot."
- **Inputs used:** rules_stakes (FAIL band), narration (explicitly fruitless search), active_threads (1 thread)

#### Turn 3 — GOOD
- **Decision:** Advanced metallic_wreckage, created "valuable find could attract scavengers" opportunity, added junction_box_salvage event
- **Assessment:** Excellent. The band was CRIT_SUCCESS. The extractor correctly identified the engagement, added the found components as a recent event, and proactively created a new opportunity about scavenger risk. The gm_beat about Richard White being reckless was well-grounded.
- **Inputs used:** rules_stakes (CRIT_SUCCESS band), narration (explicitly found components), inventory (copper_wire + capacitors added), active_threads (1 thread)

#### Turn 4 — GOOD
- **Decision:** Advanced metallic_wreckage again, created "Joe Salazar might offer contract" opportunity, added filtration_system_stabilized event
- **Assessment:** Correct. The band was SUCCESS. The player installed the components into the filtration system. The extractor correctly saw this as a second engagement with the same thread. The new opportunity about Joe was well-timed.
- **Inputs used:** rules_stakes (SUCCESS band), narration (explicitly installed components), inventory (copper_wire + capacitors removed), active_threads (1 thread), pending_beat (carried from T3)

#### Turn 5 — GOOD
- **Decision:** Ignored both metallic_wreckage and valuable_find, created "failing cooling pumps" opportunity, added secondary_grid_failure pressure
- **Assessment:** Correct. The player had no dice roll (no check.required). The intent was "show tech to Joe." Neither thread was genuinely engaged. The extractor correctly ignored both and proactively added a new pressure from the narration's "power surge" mention.
- **Inputs used:** player_intent (persuade, no check), narration (shows tech to Joe, mentions power surge), active_threads (2 threads)

#### Turn 6 — GOOD
- **Decision:** Advanced joe_salazar, ignored metallic_wreckage and valuable_find, added voltage_stabilization_success event
- **Assessment:** Correct. The band was SUCCESS. The player was diagnosing the surge with a multimeter. This indirectly helped Joe (who was present), so advancing that thread was appropriate. The metallic_wreckage thread was correctly ignored — its objective was already materially accomplished.
- **Inputs used:** rules_stakes (SUCCESS band), narration (diagnosing surge), active_threads (3 threads), narration_directive (Breathe), deescalation

### What the extractor did well

1. **Correctly distinguished engagement from non-engagement.** In T5, when the player was showing tech to Joe (not engaging any thread), the extractor correctly ignored both metallic_wreckage and valuable_find.

2. **Proactive opportunity creation.** Created 4 candidate_opportunities across 6 turns, each grounded in the narration. These became new latent threads.

3. **Scene pressure management.** Added secondary_grid_failure at T5 and updated it at T6. This shows the extractor can create and evolve pressures from narrative causality.

4. **GM beat discipline.** Emitted beats only when warranted (T3, T4, T5), with specific instructions tied to existing NPCs.

5. **Recent events discipline.** Added events only when narratively significant facts changed. Updated existing events when appropriate (T5 updated filtration_system_stabilized).

6. **Rules-outcome guidance followed.** Never marked "advanced" when band was FAIL (T2). Correctly advanced on SUCCESS/CRIT_SUCCESS (T3, T4, T6).

7. **Drift analysis consistency.** Emitted one entry per active thread each turn, with match/mismatch reasoning.

### What the extractor didn't do

1. **Evolve thread summaries.** The metallic_wreckage summary stayed "wreckage may contain circuitry" through T6 even after components were found (T3) and installed (T4). The extractor had no mechanism to update thread summaries — it only emitted signals.

2. **Create new threads from pressures.** The secondary_grid_failure pressure at T5 could have become a new candidate_opportunity (e.g., "secondary grid instability threatens infirmary"). Instead, the extractor created "failing cooling pumps present new opportunity" which was similar but didn't directly reference the pressure.

3. **Signal the metallic_wreckage thread at T6.** The player was diagnosing the surge with a multimeter at the water works. While this didn't directly engage the metallic_wreckage thread (its objective was already accomplished), the extractor could have emitted "blocked" or "ignored" with a reason. It did emit "ignored" in T5 but not T6.

4. **Create new threads per narrative phase.** The metallic_wreckage thread covered "finding → installing → testing" as a single 0→3 track. When the objective shifted from "finding" (T3) to "installing" (T4), a new thread might have been more appropriate.

### Input-output mapping quality

| Input | Used? | How |
|-------|-------|-----|
| active_threads | Yes | Evaluated each thread for engagement |
| player_intent | Yes | Checked if intent matched thread objectives |
| narration | Yes | Grounded all signals and opportunities in narration |
| rules_stakes | Yes | Never advanced on FAIL band |
| inventory changes | Yes | Noted component addition (T3) and removal (T4) |
| recent_events | Yes | Avoided duplicating existing events |
| gm_beat / pending_beat | Yes | Handled beat lifecycle correctly |
| scene pressures | Yes | Created and updated pressures |
| narration_directive | Yes (T6) | Respected "Breathe" directive |
| deescalation | Yes (T6) | Respected de-escalation signals |

### Overall assessment

The progress extractor worked **well** across 6 turns. It had all the inputs it needed and made sound decisions about what to signal, what to ignore, and what new opportunities to create.

The main limitation is structural: the extractor can emit `thread_signals` (with only `id` + `signal`), but it cannot modify thread summaries. This means thread summaries become stale as objectives evolve. The extractor correctly identified engagements and milestones, but had no way to communicate "this thread's objective has changed from X to Y."

The extractor also didn't create new threads from scene pressures, which could have given the system more active threads to work with. The secondary_grid_failure pressure at T5 was a significant narrative development that could have spawned a new thread.

---

## Recommendations

1. **Add a `thread_update` signal type** — Lets the progress extractor modify summary + progress together. When a thread's objective materially changes, the extractor can evolve the summary (e.g., "wreckage may contain circuitry" → "components found, need installation") and increment progress in one signal.

2. **Fix the progress extractor prompt** — Instruct the extractor to emit signals whenever a thread's objective materially changes, even if the outcome is "blocked." The thread was signaled at T3 but not T4 when installation happened.

3. **Create new threads per narrative phase** — When the objective changes substantially (finding → installing → testing), emit a new `candidate_opportunity` instead of reusing the same thread.

4. **Auto-complete on material state changes** — In `_apply_thread_signals`, check if a thread's objective is materially accomplished (e.g., inventory items matching the thread summary are consumed via `inventory_remove`).

See plans/ for potential implementation designs.
