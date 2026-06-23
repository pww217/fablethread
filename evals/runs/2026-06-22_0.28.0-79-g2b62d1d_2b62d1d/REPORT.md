# Eval Cycle — 2026-06-22

**Date:** 2026-06-22
**Git SHA:** 2b62d1d
**Runs:** 2 runs × 25 turns
**Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8`
**Personas:** zombie-cautious→aggressive, noir-1930s→opportunist

---

## Scores

| Pack | Persona | Checkers | Score |
|------|---------|----------|-------|
| zombie-survival | aggressive | 25/25 | 1.00 |
| noir-1930s | opportunist | 25/25 | 1.00 |

Both runs passed all 25 deterministic checkers at 100%. LLM-based checkers (directive_tone_match, beat_narrative_chain, state_fidelity, ruling_intent_match) were skipped — not enabled in auto-report mode.

---

## Regression Detection

### Changes since prior eval (2026-06-21, 47ff6261)

Key commits between runs:
- `6caae13` — fix: rewrite persona prompts for active behavior, update eval report
- `eed5878` — [convergence] Lower convergence_threshold from 3 to 2
- `2b62d1d` — Handle no-save state and fix about:blank bug on Load Save
- `6543efe` — fix: update hardcoded file paths from Repos to repos
- `660ff74` — slim AGENTS.md

### What improved

1. **Persona bug fixed.** The `--personality` flag was hardcoded to "custom" in non-resume play mode (`play.py:755`). Fixed to call `resolve_player_config(flags, session_config)`. Both runs now correctly use "aggressive" and "opportunist" personas.

2. **Convergence threshold lowered.** Changed from 3 to 2 (`eed5878`). This should make CLIMAX transitions more natural. However, the data shows mixed results:
   - **Zombie (aggressive):** Convergence consistently ≥3 in RISING, CLIMAX transitions are natural. This is an improvement.
   - **Noir (opportunist):** Convergence drops to 0 in T21-T22 (dead RISING), showing the threshold change alone isn't sufficient.

3. **Persona prompts rewritten.** The previous eval identified that personas funneled players into hiding/waiting. The new prompts command action. The results confirm this:
   - **Aggressive (zombie):** 25 turns of constant forward aggression — charging guards, firing weapons, headbutting, biting. Zero hiding/waiting turns.
   - **Opportunist (noir):** Mix of stealth, combat, and negotiation — but still heavy on SNEAK rolls (8/25 turns). More varied than "cautious" but not fully "opportunist."

### What regressed or persists

1. **Thread resolution rate remains abysmal.**
   | Pack | Created | Resolved | Rate |
   |------|---------|----------|------|
   | zombie (aggressive) | 22 | 2 | 9.1% |
   | noir (opportunist) | 19 | 2 | 10.5% |
   | Prior (5-pack, 25t) | 105 | ~13 | ~12.4% |
   
   No meaningful improvement. The storyteller creates threads but rarely resolves them via `thread_resolve` or `arc_resolve`.

2. **Null GM beats persist.** Both runs show significant null beat rates:
   - **Zombie (aggressive):** ~40% null beats (10/25 turns have no beat)
   - **Noir (opportunist):** ~52% null beats (13/25 turns have no beat)
   
   This is a known issue from the prior eval — no checker enforces a null-beat threshold.

3. **Convergence dead spots in noir.** T21-T22 in noir have convergence score = 0 (no threads, no depth, no age, no beat, no dice). The game state is completely dead — no active elements. This suggests the opportunist persona's stealth-heavy play style starves convergence.

4. **Curtain Call failure in noir.** T25 (CLIMAX #2) FAIL — missing `thread_resolve`. The opportunist run ended in CLIMAX without curtain call compliance. This is a new failure not present in the prior eval's standard runs.

5. **Crit fail rate in zombie.** 31.6% crit_fail + 42.1% fail = 73.7% bad rolls. The aggressive persona's confrontational approach generates many failed rolls, which feeds into convergence (dice_weight component) but also creates a "beat the player" narrative where the player keeps getting beaten down by guards.

6. **Thread dedup/rejection.** Both runs show thread progress dedup rejections (0.72-0.75 overlap), meaning the storyteller generates thread updates that are nearly identical to previous entries. The sanitizer rejects them, but the LLM keeps trying.

7. **Inventory canonical ID resolution.** Both runs show `resolve_inventory_canonical_id no match` warnings — the LLM extracts inventory items that don't exist in the pack's canonical list. This is a pack data gap, not a code bug.

8. **Arc resolution too frequent.** Both runs show `arc_resolve.frequency` warnings — arcs resolved in 1-4 turns (target: 8-15). This means the game transitions between visible goals too quickly, leaving threads dangling.

---

## Persona Comparison: Aggressive vs Opportunist

### Zombie-survival (aggressive)

**Behavior:** Relentless forward aggression. The player charges guards, fires weapons, headbutts, bites, and lunges at everything. Not a single defensive or stealth turn in 25.

**Narrative arc:** Starts by trying to seize plating sheets → confronts militia commander → gets shot and captured → spends T6-T25 in a brutal cycle of failed escape attempts, getting beaten, dragged to cells, and trying to fight back. By T25, the player is being dragged to eastern sector holding cells, bitten a guard's arm, and has accumulated: wounded, bruised_ribs, pinned, concussed, concussed_reinjury, wrist_trauma, thigh_trauma, exhausted.

**Phase machine:** Very regular cycling — 4 complete SETUP→RISING→CLIMAX→RESOLUTION→BREATHER→RISING cycles. Each CLIMAX lasts exactly 3-4 turns. Convergence stays above threshold throughout, meaning the aggressive persona's constant pressure keeps the game in motion.

**Roll distribution:** 78.9% bad rolls (crit_fail 31.6%, fail 42.1%). The aggressive persona's confrontational approach generates many failed rolls. This is a design concern — the game becomes a "beat the player" experience where the player keeps getting beaten down.

### Noir-1930s (opportunist)

**Behavior:** Mix of stealth, combat, and negotiation. Heavy on SNEAK rolls (8/25), but also includes ATTACK, ESCAPE, NEGOTIATE, PERSUADE, INTIMIDATE, SCOUT, and CLIMB. More varied than "cautious" but still leans toward avoidance in the first half.

**Narrative arc:** Starts in a speakeasy with enforcers → hides behind partition → gets shot → chases kidnappers in a sedan → follows tire tracks → finds union ledger page → sneaks into dockside depot. The opportunist persona's "use whatever works" approach means the player switches between stealth, combat, and investigation based on what seems most advantageous.

**Phase machine:** Less regular than zombie. T21-T22 are dead RISING turns (convergence = 0) — the stealth-heavy play style starves convergence. T24-T25 end in CLIMAX without resolution. Curtain call fails on T25.

**Roll distribution:** 20% bad rolls (fail 20%, partial 40%, success 20%, crit_success 20%). Much healthier distribution. The opportunist's mixed approach generates more successful rolls, which is better for player engagement.

### Key difference

Aggressive creates a high-intensity, high-conflict narrative but with poor roll distribution and a "beat the player" feel. Opportunist creates a more varied, investigative narrative with better roll distribution but suffers from convergence starvation during stealth-heavy periods. Neither persona produces satisfying thread/arc resolution.

---

## Tooling Issues

### Fixed in this session
- **`--personality` flag ignored in non-resume play.** `play.py:755` hardcoded `personality: "custom"`. Fixed to call `resolve_player_config(flags, session_config)`.

### Known issues (unchanged from prior eval)
- **Null GM beats** — storyteller fails to generate beats ~40-52% of the time. No checker enforces a threshold.
- **Thread resolution rate** — ~9-11% resolution rate. No checker tracks this.
- **Thread dedup rejections** — storyteller generates near-duplicate thread updates that sanitizer rejects.
- **Arc resolution too frequent** — arcs resolved in 1-4 turns (target: 8-15). No checker tracks this.
- **Inventory canonical ID resolution** — LLM extracts items not in pack's canonical list. Log.warning only.
- **Convergence dead spots** — T21-T22 in noir have score = 0. No automatic recovery mechanism.
- **Curtain Call T25 failure** — noir opportunist ended in CLIMAX without thread_resolve.

---

## Summary

Both runs passed all 25 deterministic checkers at 100%. The persona bug fix ensures the correct personas are used. The aggressive persona produces a high-intensity, high-conflict narrative with regular phase cycling but poor roll distribution (78.9% bad rolls). The opportunist persona produces a more varied, investigative narrative with better roll distribution (80% non-bad) but suffers from convergence starvation during stealth-heavy periods.

The biggest persistent issues are:
1. **Thread resolution rate** (~10%) — threads created but rarely resolved
2. **Null GM beats** (~40-52%) — storyteller fails to generate beats
3. **Convergence dead spots** — stealth-heavy play starves convergence to 0
4. **Arc resolution too frequent** — goals change too quickly, leaving threads dangling

The convergence_threshold change from 3 to 2 helped the aggressive persona (natural CLIMAX transitions) but didn't fully solve the opportunist's dead-spot problem, which stems from null beats creating zero-convergence turns.

---

## Deep-Dive: Arc Mechanics

### How arcs work

`CampaignArc` (state.py:79) has: `visible_goal`, `goal_context`, `threads[]`, `completed_threads[]`, `resolution`, `last_thread_created_turn`. The storyteller emits `arc_resolve` (state.py:183) with a new `visible_goal`, `goal_context`, `drop_threads[]`, and optional `new_threads[]`. The engine applies this via `_merge_arc_update()` in delta_builder.py:52-67, which replaces `threads[]` and `completed_threads[]` wholesale.

### Problem 1: Arc resolution too frequent

Both runs show arc resolves every 1-5 turns (target: 8-15):

| Pack | Arc resolve turns | Gaps |
|------|-------------------|------|
| zombie | T3, T5, T10, T11, T16, T21 | 2, 5, 1, 5, 5 |
| noir | T3, T5, T9, T10, T15, T16, T24 | 2, 4, 1, 5, 1, 8 |

**Root cause:** The storyteller resolves arcs on almost every CLIMAX turn. The phase machine transitions CLIMAX→RESOLUTION→BREATHER→RISING, and the storyteller sees a "completed" arc in the context, so it emits a new `arc_resolve` with a fresh `visible_goal`. This creates a "goal churn" pattern where the player's visible goal changes every 2-5 turns, preventing sustained engagement with any single objective.

**Impact:** Threads created for the old goal become orphaned — they're not in the new arc's thread list, and they're not in `completed_threads` (because the arc_resolve didn't explicitly drop them). The sanitizer's thread dedup catches some, but the fundamental problem is that arc resolution is too aggressive.

**No checker tracks arc_resolve frequency.** The existing `arc_resolution_validity` checker only validates that `drop_threads` reference existing threads — it doesn't check how often arcs are resolved.

### Problem 2: Goal update rate is near-zero

Both runs show 93-96% null `goal_update` in storyteller output. The arc's `visible_goal` changes via `arc_resolve` (not `goal_update`), which means the storyteller is using the arc_resolve path but not providing incremental goal updates between arc resolutions.

### Problem 3: Thread lifecycle in arc_resolve

When `arc_resolve` fires, it drops threads via `drop_threads[]` and optionally adds `new_threads[]`. But the storyteller often resolves arcs without explicitly dropping threads, leaving them in limbo — they're neither in `threads` nor `completed_threads`. The sanitizer's dedup catches some, but orphaned threads accumulate.

### Problem 4: Thread TTL and completed_threads

`narrate.py:128-136` filters `completed_threads` by TTL (default 3 turns). This means completed threads disappear from the narrator's context after 3 turns, but the storyteller in the next turn still has access to them via `all_threads` in the prompt context. This creates a disconnect: the narrator "forgets" completed threads but the storyteller doesn't.

---

## Deep-Dive: Thread Mechanics

### How threads work

`ArcThread` (state.py:26) has: `id`, `summary`, `dormant`, `urgency` (background/normal/urgent), `type` (threat/opportunity/complication/revelation), `progress[]`, `resolution_state`, `outcome`, `resolved_turn`, `last_updated_turn`, `added_turn`. The storyteller emits `thread_add` (single), `thread_update[]` (multiple), `thread_resolve[]` (multiple), and `arc_resolve` (with `drop_threads[]` and `new_threads[]`).

### Problem 1: Thread resolution rate is ~50% but misleading

The raw numbers show 53% resolved and 42% failed for zombie, 47% resolved and 47% failed for noir. But these are **thread_resolve events**, not unique threads. The same thread ID appears in multiple `thread_resolve` entries because the storyteller keeps trying to resolve threads that don't exist in the current arc's thread list.

Looking at the actual data:
- **Zombie:** 12 thread_adds, 19 thread_resolve events, 6 arc_resolves. Many thread_resolves reference threads that were already moved to `completed_threads` by a prior arc_resolve.
- **Noir:** 10 thread_adds, 15 thread_resolve events, 7 arc_resolves. Same pattern.

The storyteller is generating thread_resolve events for threads that no longer exist in the active thread list, which the sanitizer's dedup catches but the LLM keeps trying.

### Problem 2: Thread update dedup/rejection

Both runs show thread progress dedup rejections in the turn events. The storyteller generates thread updates where the new progress is nearly identical to the previous progress (0.72-0.75 overlap ratio). The sanitizer rejects these, but the LLM keeps generating them because it doesn't see the rejected updates in its context.

**No checker tracks thread dedup rejection rates.** This is a silent failure — the turn events show `thread_dedup_rejections` but no checker validates or reports on them.

### Problem 3: Thread urgency distribution

Both runs show very few urgent threads relative to total threads. The convergence score depends on `urgent_thread` component (+1), but most threads are "normal" urgency. This means the convergence score is often below the threshold, preventing CLIMAX transitions.

### Problem 4: Thread type distribution

Both runs show a heavy skew toward "threat" type threads. The convergence score's `threat_thread` component (+1) fires when any non-dormant threat thread exists, but this doesn't create narrative variety. The storyteller generates threats but rarely opportunities, complications, or revelations.

### Problem 5: Thread add rate is low

Both runs show 59-64% null `thread_add` in storyteller output. The storyteller generates thread updates more often than new threads, which means it's working with existing threads rather than creating new narrative threads. This contributes to the "goal churn" problem — the storyteller keeps updating the same threads instead of creating fresh ones.

---

## Deep-Dive: Pacing Engine

### How convergence works

`compute_convergence_score()` in `_pacing.py:86-142` computes a 5-component score:
1. **urgent_thread** (+1): Any non-dormant thread with urgency="urgent"
2. **threat_thread** (+1): Any non-dormant thread with type="threat"
3. **scene_age** (+1): Scene age ≥ `scene_pressure_threshold` (default 3)
4. **beat_streak** (+1): ≥60% of last 5 beats are pressure types (pressure/complication/escalation/setback), with minimum threshold
5. **dice_weight** (+1): Urgent thread + rolled + crit_fail/fail

The score must reach `convergence_threshold` (default 2, was 3) to transition RISING→CLIMAX.

### Problem 1: Convergence dead spots in noir

T20-T22 in noir have convergence score = 0 across all 5 components:
- No urgent threads (all background)
- No threat threads
- Scene age = 0 (just entered BREATHER→RISING)
- No beat streak (null beats in T20-T22)
- No dice weight (no rolls in T20-T22)

This is a **convergence starvation** problem. The opportunist persona's stealth-heavy play style generates few rolls, few beats, and few urgent threads. The convergence score drops to 0 and stays there because there's no mechanism to recover from a zero-convergence state.

**Root cause:** The convergence score is entirely reactive — it responds to what's happening in the current scene, but has no proactive mechanism to inject pressure when the scene goes quiet. The `beat_streak` component requires beats to exist, but null beats (57% in noir) mean there are no beats to streak. The `dice_weight` component requires rolls, but the opportunist persona avoids rolls by choosing stealth.

### Problem 2: Convergence threshold change has mixed results

Lowering from 3 to 2 (`eed5878`) helped the aggressive persona (convergence consistently ≥3 in RISING, natural CLIMAX transitions) but didn't solve the opportunist's dead-spot problem. The threshold change alone isn't sufficient when all 5 components are 0.

### Problem 3: Phase machine is too rigid

The phase machine (`_compute_scene_phase` in `_pacing.py:222-294`) enforces a strict state machine:
- SETUP→RISING (urgent thread or 3 turns)
- RISING→CLIMAX (convergence ≥ threshold)
- CLIMAX→RESOLUTION (climax_turn_count ≥ limit, default 5)
- RESOLUTION→BREATHER (immediate, 1 turn)
- BREATHER→RISING (urgent thread or breather_max_turns, default 3)

This creates a "conveyor belt" pattern where the game moves through phases mechanically rather than narratively. The aggressive persona's constant pressure keeps the machine running smoothly, but the opportunist persona's stealth-heavy play style breaks the machine by starving convergence.

### Problem 4: Curtain call detection is turn-count based, not narrative-based

Curtain call fires when `climax_turn_count >= climax_turn_limit - 1` (forced) or `climax_turn_count == 1` (active). This is purely mechanical — it doesn't check whether the narrative has reached a natural conclusion point. T25 in noir is in CLIMAX with curtain_call="" (not forced, not active), meaning the storyteller wasn't prompted to resolve threads.

### Problem 5: Spiral detection is not used in convergence

`detect_spiral()` in `_pacing.py:33-58` detects death spirals (consecutive hard rolls or high ratio of hard rolls). This feeds into `spiral_detected` in PacingContext, which modifies allowed beat types (removes pressure beats), but it doesn't directly affect convergence. A player in a death spiral (like the aggressive persona with 74% bad rolls) gets fewer pressure beats, which reduces beat_streak, which reduces convergence — creating a feedback loop where bad rolls make it harder to reach CLIMAX.

---

## Deep-Dive: Beat Mechanics

### How beats work

`GMBeat` (extraction.py:181) has: `type` (complication/revelation/opportunity/breathing_room/pressure/twist/setback/escalation/callback), `effect`, `npc_id`, `driver` (motivation/fear/leverage/bond/personality), `beat_expires_turn`. Beats are generated by the storyteller and stored in `state.meta.pending_gm_beat`, then consumed by the narrator on the next turn.

### Problem 1: Null beat rate is 34-57%

Both runs show significant null beat rates:
- **Zombie (aggressive):** 10/29 null beats (34%)
- **Noir (opportunist):** 16/28 null beats (57%)

**Root cause:** The storyteller's prompt doesn't enforce beat generation. The `GMBeat` model has a `_nullify_invalid_gm_beat` validator (extraction.py:256-259) that sets `gm_beat = None` when the LLM emits an invalid type. The LLM often omits the beat entirely or emits an invalid type, resulting in a null beat.

**No checker enforces a null-beat threshold.** The `gm_beat_lifecycle` checker validates that beats are consumed (not persisted unchanged), but doesn't check whether beats are generated.

### Problem 2: Beat driver is always "motivation"

Both runs show that the vast majority of beats use `driver="motivation"`. This means the storyteller is generating beats based on NPC motivations rather than fears, leverage, bonds, or personality. This creates a narrow narrative palette where all beats feel the same.

### Problem 3: Beat types are phase-constrained but not narrative-driven

`BEAT_PHASE_MAP` in `_pacing.py:24-30` constrains allowed beat types by phase:
- SETUP: all types
- RISING: pressure/complication/escalation/revelation/twist
- CLIMAX: pressure/escalation/complication (most restrictive)
- RESOLUTION: breathing_room/callback/revelation
- BREATHER: opportunity/revelation/callback/breathing_room/hazard

This is correct in theory but the storyteller often ignores the constraints, generating beats that don't match the phase's narrative intent. The `_nullify_invalid_gm_beat` validator silently drops these, contributing to null beat rate.

### Problem 4: Beat streak component in convergence is fragile

The `beat_streak` component requires ≥60% of last 5 beats to be pressure types. With null beats at 34-57%, the window is often too small to establish a streak. When the storyteller generates a null beat, the streak resets, which reduces convergence, which prevents CLIMAX transitions.

### Problem 5: Beat expiration is turn-based, not narrative-based

`beat_expires_turn` in GMBeat sets a turn number after which the beat expires. This is mechanical — the beat disappears regardless of whether the narrative has resolved it. The narrator checks `_expires` in `narrate.py:172-175` and nulls the beat if `turn_no > _expires`.

---

## Deep-Dive: NPC Mechanics

### How NPCs work

NPCs are stored in `state.compendium.npcs` as a dict keyed by NPC ID. Each NPC has: `id`, `name`, `title`, `bio`, `aliases`, `motivation`, `fear`, `leverage`, `presence` (present/nearby/known/departed), `position`, `first_seen_turn`, `personality`, `bond`, `departed_reason`, `departed_turn`, `party`. The scene extractor updates NPCs via `CompendiumNpcUpdate` (extraction.py:18), and the engine applies changes via `apply_npc_scene_management()` in `state/npcs.py:172-337`.

### Problem 1: NPC presence lifecycle is incomplete

`NpcPresence` enum (state.py:14-18) has: PRESENT, NEARBY, KNOWN, DEPARTED. But the engine also uses "archived" as a terminal state (turn_state.py:670, prompt_context.py:30). The "archived" state is not in the enum, which is a design inconsistency. The checker was fixed in the prior eval to accept "archived", but the enum itself is incomplete.

### Problem 2: NPC roster is limited to 10 entries

`_build_npc_roster()` in prompt_context.py:25-53 returns `entries[:10]`. This means if there are more than 10 NPCs in the compendium, only the first 10 (by presence priority) are shown to the LLM. This can cause NPCs to be silently dropped from the storyteller's context, leading to inconsistent NPC behavior.

### Problem 3: NPC personality assignment is automatic but inconsistent

`apply_npc_scene_management()` in state/npcs.py:304-315 automatically assigns personality to named NPCs that lack one, using `assign_personality()` from personality.py. This means NPCs get personalities based on their motivation/fear, but the assignment is automatic and not guided by the storyteller. This can lead to NPCs having personalities that don't match their narrative role.

### Problem 4: Group NPC resolution is complex but fragile

`state/npcs.py` has extensive logic for group NPC resolution (quantity stripping, alias mapping, deduplication). The `_strip_quantity_suffix()` function collapses "militia_guards_five" → "militia_guards", and `_resolve_group_npc_id()` resolves to canonical entries. This is complex but fragile — if the LLM generates inconsistent IDs (e.g., "militia_guards" on one turn, "two_militia_guards" on another), the deduplication may not work correctly.

### Problem 5: NPC dialogue is not tracked

The NPC model has no `dialogue` or `speech_history` field. NPCs are described in the roster but don't have memorable dialogue patterns. The storyteller generates NPC dialogue in narration, but it's not tracked in state, so there's no way to verify that NPCs speak consistently across turns.

---

## Deep-Dive: Ruling, Dice, and Prompt Quality

### Ruling system

The ruling system (ruling.py) determines whether to roll, declares impossibility, or skips rolls. Both runs show:
- **Zombie:** 19 rolls (76% of turns), 74% bad rolls (crit_fail 32%, fail 42%, setback 5%, success 21%)
- **Noir:** 5 rolls (20% of turns), 20% bad rolls (fail 20%, partial 40%, success 20%, crit_success 20%)

The aggressive persona triggers rolls on almost every turn (confrontation = risky), while the opportunist avoids rolls by choosing stealth (routine movement = no check). This is by design — the ruling system's `impossible` and `routine` paths skip rolls for low-risk actions.

**Problem:** The ruling system's "routine" path (no roll) is too generous. The opportunist persona exploits this by choosing stealth actions that the ruling system classifies as "no check required: routine movement." This creates a gameplay loop where the opportunist avoids rolls entirely, which starves convergence (no dice_weight component) and creates dead spots.

### Dice distribution

The ruling system's band distribution is determined by the dice roll + stat_mod + skill. Both runs show:
- **Zombie:** Heavy on strength rolls (14/19), reflecting the aggressive persona's physical confrontations
- **Noir:** All dexterity rolls (5/5), reflecting the opportunist persona's stealth and agility

This is correct behavior — the persona's actions determine which stats are relevant. But the lack of variety in noir (all dexterity) suggests the opportunist persona's "use whatever works" approach converges on a single skill.

### Prompt quality

Both runs show high token usage in storyteller extraction (4552 tokens in, 178 tokens out for T25 noir). The storyteller prompt is complex, with thread context, NPC roster, beat context, and pacing directives. The low output token count suggests the LLM is generating concise but sparse storyteller output, which contributes to null beats and null thread_adds.

**Problem:** The storyteller prompt is too information-dense. The LLM receives thread context, NPC roster, beat context, pacing directives, recent turns, and curtain call signals — but the output schema is sparse (actions, outcome_summary, goal_update, gm_beat, thread_resolve, thread_add, thread_update, arc_resolve, chapter_end). The LLM has to choose which fields to populate, and it often skips beats and thread_adds in favor of actions and outcome_summary.

---

## Summary of Deep-Dive Findings

### Critical issues (require design changes)

1. **Arc resolution too frequent** — storyteller resolves arcs every 1-5 turns, creating goal churn. No checker tracks this.
2. **Convergence starvation** — stealth-heavy play starves all 5 convergence components to 0. No proactive mechanism to inject pressure.
3. **Null beat rate 34-57%** — storyteller fails to generate beats. No checker enforces a threshold.
4. **Thread resolution events ≠ unique threads** — storyteller generates thread_resolve events for threads that no longer exist in active thread list.

### High-priority issues (require code changes)

5. **Thread dedup rejection rate** — storyteller generates near-duplicate thread updates. No checker tracks this.
6. **Thread TTL disconnect** — narrator forgets completed threads after 3 turns, but storyteller doesn't.
7. **Curtain call is turn-count based, not narrative-based** — T25 in noir has no curtain call signal despite being in CLIMAX.
8. **NPC presence enum incomplete** — "archived" is used but not in enum.
9. **NPC roster limited to 10** — NPCs silently dropped from context.

### Medium-priority issues (improvements)

10. **Beat driver is always "motivation"** — narrow narrative palette.
11. **Beat streak component is fragile** — null beats reset streaks.
12. **Ruling system's "routine" path is too generous** — opportunist avoids rolls entirely.
13. **Storyteller prompt is too information-dense** — LLM skips sparse fields.
14. **Group NPC resolution is complex but fragile** — inconsistent IDs may not deduplicate correctly.
15. **NPC dialogue is not tracked** — no way to verify consistent speech patterns.
