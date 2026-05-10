# Eval Report — `full_cycle`

**Pack:** `eval-pack` · **Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8` · **Temp override:** `None`  
**Started:** 2026-05-10T21:10:31.947413+00:00 · **Finished:** 2026-05-10T21:17:20.791059+00:00  
**Output dir:** `/Users/pwilson/Repos/ccya/evals/runs/20260510T211031Z_n2gg1cf3`  
**Compared against:** _(no prior run found)_

## Judge Summary

**Mechanical:** 3/5  
**Narrative:** 4/5  
**Rubric:** `/Users/pwilson/Repos/ccya/evals/rubrics/default.md`
**Judge model:** `mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit`

**Pipeline scores:**
- rules: 4/5
- narrate: 4/5
- extract_scene: 4/5
- extract_state: 3/5
- extract_progress: 2/5

**Trace:** [`full_cycle.trace.md`](full_cycle.trace.md)
**Judge response:** [`full_cycle.judge.md`](full_cycle.judge.md)

## ✅ No flags

No regressions, retries, failures, or judge score drops detected.


## Judge Verdict (full)

# ccya Eval Judge — Default Rubric

# Storytelling Trace

### Momentum Trace
T5: band=success 0→1. Tone matches (standoff).
T6: band=setback 1→0. Tone matches (extortion).
T7: band=crit_success 0→2. Tone matches (relief/safe haven).
T9: band=fail 2→1. Tone matches (panic).
T10: band=setback 1→0. Tone matches (alarm).
T12: band=crit_success 0→2. Tone matches (escape).
Narration tone consistently aligns with momentum shifts; no wrong-direction or flat momentum on significant rolls.

### GM Beat Trace
T3: generated=pressure → T4: surfaced=yes → impact=complication
T4: generated=pressure → T5: surfaced=yes → impact=complication
T5: generated=complication → T6: surfaced=yes → impact=complication
T6: generated=escalation → T7: surfaced=yes → impact=complication
T7: generated=breathing_room → T8: surfaced=yes → impact=breathing
T8: generated=complication → T9: surfaced=yes → impact=complication
T9: generated=pressure → T10: surfaced=yes → impact=complication
T10: generated=escalation → T11: surfaced=yes → impact=complication
T11: generated=pressure → T12: surfaced=yes → impact=complication
T12: generated=breathing_room → T13: surfaced=yes → impact=breathing
All beats generated in T-N are successfully surfaced in T-N+1 with appropriate impact. No orphaned or wasted beats.

### Scene Pressure Trace
T3: added=road_toughs_presence urgency=building → escalated=no → resolved=no (sits inert until T12)
T4: added=calloway_confrontation urgency=immediate → escalated=no → resolved=yes (T5)
T6: added=toughs_extortion_escalation urgency=immediate → escalated=no → resolved=yes (T7)
T9: added=matthew_alarm urgency=immediate → escalated=no → resolved=yes (T10)
T11: added=combat_in_service_corridor urgency=immediate → escalated=no → resolved=yes (T12)
T13: added=pursuers_approaching urgency=immediate → escalated=no → resolved=no
Pressures escalate logically. `road_toughs_presence` sits inert across multiple turns, which is acceptable for a background threat, but could be nudged earlier.

### Condition Lifecycle Trace
T1: added=bruised_ribs, low_morale → T13: still_present=yes → resolved=no
T9: added=shaken → T12: still_present=no → resolved=yes (auto-removed by engine/state)
T11: added=wounded → T13: still_present=yes → resolved=no
Conditions persist until resolved or auto-removed. No silent disappearances outside engine TTL.

### Quest Arc Trace
T1: created=settle_the_debt → T2: objectives_done=[1,2] → resolved=completed
T3: created=deliver_the_ledger → T7: objectives_done=[1,2,3] → resolved=completed (T8)
T3: created=clear_the_road_toughs → T7: objectives_done=[1,2] → resolved=completed
T8: created=deliver_halden_ledger (DUPLICATE) → T12: objectives_done=[] → resolved=completed (FAIL: duplicate quest ID created despite existing `deliver_the_ledger`)

### Inventory Evolution Trace
T2: remove credits qty=500. Narration reflected.
T3: add ledger qty=1. Narration reflected.
T7: remove ledger qty=1. Narration reflected.
T11: add silver_pocket_watch qty=1. Narration reflected.
T13: spending coins mentioned ("pulling a few meager coins") but no `inventory_remove` extracted. Flagged.

# State Evolution Trace

### State Coherence
State evolves logically across turns. Inventory matches gains/losses. Conditions persist until resolved. Pressures escalate and resolve as narrated. Quests advance toward completion.

### State Drift
T12 state shows `deliver_halden_ledger` completed, but T8 already completed `deliver_the_ledger`. This is a duplicate quest ID drift caused by the progress extractor failing the mandatory dedup rule. T12 state also shows `shaken` removed, which aligns with engine auto-removal, but the trace doesn't explicitly show the removal trigger.

### State Completeness
T13 narration describes spending coins, but the state extractor emits no `inventory_remove`. This is a missing update from the state pipeline. All other domains (location, NPCs, pressures) update correctly.

# Mechanical Design Critique

### Rules
**What Went Well:** Intent classification is precise. `check.required` correctly defaults to false for routine commerce (T2) and exploration (T1, T3, T8, T13). Dice resolution maps cleanly to bands, and directives accurately shape narrator latitude (e.g., T5 success → standoff, T9 fail → panic).
**What Went Poorly:** Minor token bloat in the rules prompt with redundant difficulty/stat definitions that could be condensed. No major mechanical failures.

### Narrate
**What Went Well:** Prose consistently honors dice bands and directives. T7's `breathing_room` directive is beautifully realized in the inn's warmth. T12's `CRIT_SUCCESS` escape is vivid and kinetic. Scope tail emission is accurate, gating downstream extractors correctly.
**What Went Poorly:** Occasional over-reliance on atmospheric descriptors ("damp, predatory night", "amber glow") that slightly slow pacing. The narrator sometimes repeats location details already in the prompt, though this is mitigated by the scope system.

### Extract Scene
**What Went Well:** NPC presence tracking is robust. `npc_add`/`npc_remove` correctly handles arrivals/departures (T3 Caron leaves, T7 toughs leave, T13 Melvin arrives). Location changes are captured accurately with appropriate descriptions.
**What Went Poorly:** `npc_update` sometimes misses attitude shifts that are clearly narrated (e.g., T10 Matthew's shift from panicked to accusatory is captured, but T11 Matthew's dazed state is only captured in `npc_update` alongside `tavern_patrons`, which could be cleaner).

### Extract State
**What Went Well:** Inventory delta accuracy is high. Explicit numbers are extracted correctly (T2: 500 credits, T11: 1 watch). Condition lifecycle is handled properly, respecting roll context (T11 partial strength → `wounded`).
**What Went Poorly:** T13 spending action extraction failure. Narration explicitly says "pulling a few meager coins from your pouch", but the extractor emits no `inventory_remove`. The prompt's "Priority 2 — Inference" rule is ignored here.

### Extract Progress
**What Went Well:** Quest objective tracking is generally accurate. `recent_events_add` captures key plot points. `actions` suggestions are relevant and varied. `gm_beat` generation is timely and grounded.
**What Went Poorly:** Critical quest deduplication failure. T8 completes `deliver_the_ledger`. T12 creates/completes `deliver_halden_ledger` despite the seed containing `deliver_the_ledger`. The extractor ignored the "NEVER create a new quest ID" rule. Additionally, compaction sanitization is entirely absent (no quest closes, pressure removes, or condition purges recorded).

### Prompt Analysis
The `prior_turn_narration` block is duplicated verbatim in both the Narrate and Progress prompts (confirmed by Deterministic Signals). While the narrator needs full context, the progress extractor only needs outcome context. This wastes ~1500 tokens/turn. The state prompt could also trim redundant PC bio sections.

### Mechanic Placement
All mechanics are correctly placed per the reference table. `scene_pressure_add` lives in progress. `inventory_add/remove` lives in state. `npc_add/remove` lives in scene. No scope/domain mismatches detected.

### Issues
- **Quest Deduplication Failure** (turns: 8, 12) — Failure mode: `failed to output key information`. Remediation: Pass existing active quest IDs to the progress extractor and enforce strict ID matching in the prompt. Add a pre-validation step that rejects new quest IDs overlapping existing ones.
- **Spending Action Extraction Miss** (turns: 13) — Failure mode: `failed to output key information`. Remediation: Add explicit instruction in the state prompt to scan for spending/giving verbs even without exact numbers, and default to `inventory_remove` with a vague amount or full-stack if context implies it.
- **Compactor Sanitization Miss** (turns: 6, 12) — Failure mode: `failed to output key information`. Remediation: The compactor prompt must explicitly instruct the model to cross-reference `prior_history` bullets with `state.yaml` to close completed quests, remove resolved pressures, and purge expired conditions.

### Pipeline Score
- rules: 4
- narrate: 4
- extract_scene: 4
- extract_state: 3
- extract_progress: 2

# Cross-Pipeline Correlation

### Rules → Narrate Binding
Perfect binding. T5 success → standoff. T6 setback → extortion. T7 crit success → relief. T9 fail → panic. T10 setback → alarm. T12 crit success → escape. No inversions or directive violations.

### Rules → State Extract Routing
T11 partial strength → `wounded` condition correctly extracted. Stakes routing produced observable mechanical consequences.

### Narrate → Scene Extract Consistency
T3, T7, T12 location changes correctly captured. NPC additions/removals match narration. No missed scene shifts.

### Narrate → State Extract Consistency
T2, T3, T7, T11 inventory changes correctly captured. T13 spending missed (noted above).

### Narrate → Progress Extract Consistency
T8 quest completion captured, but duplicate ID created. T12 quest completion captured with duplicate ID. Recent events and pressures correctly aligned with narration.

### State → Progress Extract Handoff
`items_gained` correctly passed to progress extractor. Used appropriately in `actions` and `outcome_summary`.

### Progress → Narrate Feedback Loop
`gm_beat` and `scene_pressure_add` from T-N consistently surface in T-N+1 narration. No broken feedback loops.

# Storytelling Design Critique

### quest_arc_quality
3/5. The main arcs (debt, ledger, toughs) resolve satisfyingly. However, the duplicate quest `deliver_halden_ledger` at T12 breaks the long-arc cohesion and suggests the engine is generating redundant objectives instead of closing the existing arc.

### rewards_and_consequences [trace]
4/5. Successes yield relief, escape, and new opportunities. Failures yield complications, alarms, and pressure escalation. The failure arc creates tension rather than dead ends.

### narrative_compellingness
4/5. High tension, clear stakes, and strong prose. Choices matter. The escape sequence (T12) is particularly well-executed.

### npc_development
4/5. Matthew Estrada evolves from startled to accusatory to tackled. Kenneth Miller enters as a disciplined professional. David Calloway shifts from defensive to greedy. NPCs react meaningfully.

### npc_voice
4/5. Distinct speech patterns: Calloway is greedy and colloquial ("piece of the pie"), Matthew is panicked and sharp, Miller is disciplined and terse. No interchangeable dialogue detected.

### world_consistency
4/5. All entities are sanctioned by the seed or compendium. No unsanctioned introductions.

### world_reactivity
4/5. The world reacts dynamically: toughs escalate, Matthew alerts the tavern, Miller intervenes, patrons converge. Consequence propagation is strong.

### player_agency
4/5. Player choices drive the plot. Failures create new options (search coat, escape, bribe). The engine honors stated actions.

### failure_arc [trace]
4/5. Failures produce lasting conditions (`shaken`, `wounded`) and escalate pressures. Negative momentum creates narrative tension. No immediately forgotten failures.

### pacing_and_pressure
4/5. Good mix of high-tension confrontations and breathing room. Momentum tone alignment is consistent.

### deescalation_mechanics
4/5. T7 and T12 deescalation respected. `breathing_room` beats preferred when `deescalate >= 0.8`. No new pressures added during deescalation turns.

### scenario_quality
4/5. Exercises all major mechanics (dice rolls, inventory, conditions, quests, pressures, GM beats, location changes). Good variety of turn types (social, combat, escape, exploration). Clear narrative arc.

# Prompt Redundancy Analysis

The `prior_turn_narration` block is duplicated verbatim in the Narrate and Progress prompts. While the narrator needs full context, the progress extractor only needs outcome context for `actions` and `outcome_summary`. This duplication wastes ~1500 tokens per turn.

**Top 3 dedup opportunities:**
1. Replace `prior_turn_narration` in the Progress prompt with a condensed `recent_turns_summary` or `outcome_context` block containing only the last 1-2 turns' key events and roll outcomes.
2. Trim the Narrate prompt's `Known Characters` and `Recent Events` sections to only include entities relevant to the current scene or active quests.
3. Consolidate the `active_quests` and `scene_pressure` sections in the Progress prompt into a single `active_context` block to reduce structural redundancy.

# Compaction Capabilities Report

- `bullet_named_npcs`: [OK] Calloway, Estrada, Miller, Melvin preserved in bullets.
- `bullet_location`: [OK] Inn, river bend, service corridor preserved.
- `bullet_quest_outcomes`: [OK] Debt cleared, ledger delivered preserved.
- `bullet_key_items`: [OK] Ledger, watch preserved.
- `bullet_conditions`: [FAIL] No conditions mentioned in compaction bullets.
- `bullet_irreversible`: [OK] Tackled, stabbed, bribes attempted preserved.
- `bullet_deaths`: [NA] No deaths occurred.
- `bullet_mech_consequences`: [OK] Extortion, alarm, pursuit preserved.
- `bullet_culling`: [OK] Dialogue and atmospherics trimmed effectively.
- `sanitize_npc_merge`: [OK] No duplicate compendium NPCs.
- `sanitize_inventory`: [OK] No duplicate items.
- `sanitize_quest_close`: [FAIL] No quest closures recorded in sanitization despite quests completing.
- `sanitize_pressure`: [FAIL] No pressure removals recorded in sanitization despite pressures resolving.
- `sanitize_condition`: [FAIL] No condition removals recorded in sanitization.

# Auto-Checker Failures

| Turn | Assertion | Detail | Why it failed | Remediation |
|---|---|---|---|---|
| 2 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Credits'] | Auto-checker only validates against `npc_add/update`, ignoring inventory items and compendium. | Low-severity auto-checker noise. No engine fix needed, but consider widening the checker's validation scope to include `state.inventory` and `compendium`. |
| 3 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Crossed'] | "Crossed" is part of the location name "Crossed Keys Inn", not an NPC. | Auto-checker noise. |
| 5 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['David', 'Calloway'] | NPCs are already in `present_npcs` from T4. Checker doesn't cross-reference `present_npcs`. | Auto-checker noise. |
| 7 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['David', 'Calloway', 'Leather'] | "Leather" is part of the inventory item name. | Auto-checker noise. |
| 8 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Estrada', 'Matthew'] | Already in `present_npcs`. | Auto-checker noise. |
| 9 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Estrada', 'Matthew'] | Already in `present_npcs`. | Auto-checker noise. |
| 10 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Estrada', 'Matthew', 'Thief'] | "Thief" is a generic descriptor. | Auto-checker noise. |
| 13 | `universal.npc_mention.extracted` | narration mentions names not in npc_add/update or known: ['Calloway', 'Nearby', 'Melvin'] | Melvin is added in T13 scene extract. "Calloway" is a surname reference. | Auto-checker noise. |

# Verdict

### Mechanical Integrity
3/5. The rules, narrate, and scene pipelines are robust. The state pipeline misses spending extractions. The progress pipeline suffers from a critical quest deduplication failure (T8/T12) and a complete lack of compactor sanitization (quest close, pressure remove, condition remove). These are structural flaws that break state coherence.

### Narrative Quality
4/5. Strong prose, excellent pacing, and meaningful NPC development. The duplicate quest at the end slightly mars the arc, but the overall fiction is compelling and reactive.

### System Cohesion
3/5. Cross-pipeline handoffs work well (Rules→Narrate, Progress→Narrate). However, the state extraction miss (T13) and quest duplication (T12) create drift. The compactor's failure to sanitize state after compaction means stale data persists in `prior_history`.

### Pipeline I/O Relevance
3/5. Rules and Narrate have focused I/O. Scene and State are mostly tight but miss spending verbs. Progress is the most bloated, receiving full `prior_turn_narration` when only outcome context is needed. The compactor prompt lacks explicit sanitization directives.

### Regression & Known Issues
No new regressions detected. The quest deduplication failure and compactor sanitization miss are confirmed structural issues that need prompt/engine fixes.

### Key Findings
1. **Quest Deduplication Failure (T8/T12):** The progress extractor created `deliver_halden_ledger` instead of closing `deliver_the_ledger`. Pass existing quest IDs to the extractor and enforce strict ID matching.
2. **Compactor Sanitization Miss (T6/T12):** No quest closes, pressure removals, or condition purges recorded. Add explicit compactor instructions to cross-reference bullets with `state.yaml`.
3. **Spending Extraction Miss (T13):** Narration describes spending coins, but no `inventory_remove` emitted. Strengthen the state prompt's spending/giving verb scanning.

# Actionable Issues Surfaced

[Engine] Quest Deduplication Failure (turns: 8, 12) — The progress extractor generated a new quest ID (`deliver_halden_ledger`) instead of updating the existing `deliver_the_ledger`. This breaks the quest arc and inflates state. Remediation: Pass the full list of active quest IDs to the progress extractor and add a mandatory pre-check in the prompt: "If the objective matches an existing quest, update that quest ID. Never create a new ID."

[Engine] Compactor Sanitization Miss (turns: 6, 12) — Compaction fires but records zero sanitization actions. Stale pressures and conditions persist in `prior_history`. Remediation: Update the compactor system prompt to explicitly instruct the model to cross-reference `prior_history` bullets with `state.yaml` and emit `quest_close`, `pressure_remove`, and `condition_remove` for resolved/expired entries.

[Prompting] State Extract Spending Miss (turns: 13) — Narration says "pulling a few meager coins from your pouch", but the extractor emits no `inventory_remove`. Remediation: Add explicit instruction in the state prompt: "Scan for spending/giving verbs even without exact numbers. If the player parts with currency or items, emit `inventory_remove` with a reasonable amount or omit `amount` for full-stack."

[Prompting] Prompt Redundancy (turns: 1-13) — `prior_turn_narration` is duplicated verbatim in Narrate and Progress prompts, wasting ~1500 tokens/turn. Remediation: Replace the full `prior_turn_narration` block in the Progress prompt with a condensed `recent_turns_summary` containing only the last 1-2 turns' key events and roll outcomes.

# Additional Observations

The auto-checker's `universal.npc_mention.extracted` failures are almost entirely false positives caused by the checker only validating against `npc_add/update` arrays, ignoring `state.scene.present_npcs`, `compendium`, and inventory/location names. While not a mechanical failure, this creates noise in the evaluation pipeline. Consider widening the checker's validation scope or suppressing these specific assertions.

The compactor's bullet generation is actually quite strong, preserving named NPCs, locations, quest outcomes, and key items effectively. The only major gap is the lack of sanitization directives, which is a prompt engineering fix rather than a structural flaw.

The engine handles deescalation and pressure lifecycle correctly, but the `road_toughs_presence` pressure sits inert from T3 to T12. While background pressures are allowed to persist, the engine could benefit from a "pressure aging" directive that nudges the narrator to reference or escalate background threats every 3-4 turns to maintain tension.

## Auto-Checker

**137 passed, 16 failed**

| Turn | Assertion | Result | Detail |
|---|---|---|---|
| 1 | `rules.rolled` | ✅ | rolled=False |
| 1 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 1 | `universal.pending_gm_beat.consumed` | ✅ | (first turn) |
| 1 | `universal.location_change.applied` | ✅ | (no change) |
| 1 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 1 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 1 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 1 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 1 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 1 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 1 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 2 | `rules.rolled` | ❌ | rolled=False |
| 2 | `extract.state.inventory_remove` | ✅ | inventory_remove[credits] amount=500 |
| 2 | `extract.progress.quest_updates` | ✅ | quest_updates[settle_the_debt] found |
| 2 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 2 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 2 | `universal.location_change.applied` | ✅ | (no change) |
| 2 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 2 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Credits'] |
| 2 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 2 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 2 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 2 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 2 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 3 | `rules.rolled` | ❌ | rolled=False |
| 3 | `extract.progress.quest_updates` | ✅ | quest_updates[deliver_the_ledger] found |
| 3 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 3 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 3 | `universal.location_change.applied` | ✅ | marrows_crossing -> marrows_crossing_street |
| 3 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 3 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 3 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 3 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 3 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 3 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 3 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 4 | `rules.rolled` | ✅ | rolled=False |
| 4 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=4 |
| 4 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 4 | `universal.location_change.applied` | ✅ | marrows_crossing_street -> crossed_keys_approach |
| 4 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 4 | `universal.npc_mention.extracted` | ✅ | 5 candidates skipped (likely locations/items, not NPCs) |
| 4 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 4 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 4 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 4 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 4 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 5 | `rules.rolled` | ✅ | rolled=True |
| 5 | `extract.scene.scene_tags` | ❌ | scene_tags[combat] not found |
| 5 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 5 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 5 | `universal.location_change.applied` | ✅ | (no change) |
| 5 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 5 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['David', 'Calloway'] |
| 5 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 5 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 5 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 5 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 5 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 6 | `rules.rolled` | ✅ | rolled=True |
| 6 | `extract.state.inventory_remove` | ❌ | inventory_remove[credits] not found |
| 6 | `extract.progress.quest_updates` | ✅ | quest_updates[clear_the_road_toughs] found |
| 6 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 6 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 6 | `universal.location_change.applied` | ✅ | (no change) |
| 6 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 6 | `universal.npc_mention.extracted` | ✅ | 5 candidates skipped (likely locations/items, not NPCs) |
| 6 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 6 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 6 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 6 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 6 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 7 | `extract.progress.quest_updates` | ✅ | quest_updates[deliver_the_ledger] found |
| 7 | `extract.progress.quest_status` | ❌ | quest[deliver_the_ledger].status='active' (expected 'completed') |
| 7 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 7 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 7 | `universal.location_change.applied` | ✅ | crossed_keys_approach -> crossed_keys_inn |
| 7 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 7 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['David', 'Calloway', 'Leather'] |
| 7 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 7 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 7 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 7 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 7 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 8 | `rules.rolled` | ✅ | rolled=True |
| 8 | `extract.state.inventory_remove` | ❌ | inventory_remove[brass_key] not found |
| 8 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=8 |
| 8 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 8 | `universal.location_change.applied` | ✅ | crossed_keys_inn -> crossed_keys_service_corridor |
| 8 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 8 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Estrada', 'Matthew'] |
| 8 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 8 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 8 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 8 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 8 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 9 | `rules.rolled` | ✅ | rolled=True |
| 9 | `extract.scene.scene_tags` | ❌ | scene_tags[social] not found |
| 9 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 9 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 9 | `universal.location_change.applied` | ✅ | (no change) |
| 9 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 9 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Estrada', 'Matthew'] |
| 9 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 9 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 9 | `universal.pc.condition_no_dupes` | ✅ | 3 conditions, no dupes |
| 9 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 9 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 10 | `rules.rolled` | ✅ | rolled=True |
| 10 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 10 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 10 | `universal.location_change.applied` | ✅ | (no change) |
| 10 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 10 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Estrada', 'Matthew', 'Thief'] |
| 10 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 10 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 10 | `universal.pc.condition_no_dupes` | ✅ | 3 conditions, no dupes |
| 10 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 10 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 11 | `rules.rolled` | ✅ | rolled=True |
| 11 | `extract.scene.scene_tags` | ✅ | scene_tags[combat] found |
| 11 | `universal.recent_events_add.turn_stamped` | ✅ | all 2 entries stamped with turn=11 |
| 11 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 11 | `universal.location_change.applied` | ✅ | (no change) |
| 11 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 11 | `universal.npc_mention.extracted` | ✅ | 4 candidates skipped (likely locations/items, not NPCs) |
| 11 | `universal.recent_events.ring_bounded` | ✅ | 6 entries |
| 11 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 11 | `universal.pc.condition_no_dupes` | ✅ | 4 conditions, no dupes |
| 11 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 11 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 12 | `rules.rolled` | ❌ | rolled=True |
| 12 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=12 |
| 12 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 12 | `universal.location_change.applied` | ✅ | crossed_keys_service_corridor -> river_bend_muddy_banks |
| 12 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 12 | `universal.npc_mention.extracted` | ✅ | 5 candidates skipped (likely locations/items, not NPCs) |
| 12 | `universal.recent_events.ring_bounded` | ✅ | 2 entries |
| 12 | `universal.scene.npc_cap` | ✅ | 0 NPCs |
| 12 | `universal.pc.condition_no_dupes` | ✅ | 3 conditions, no dupes |
| 12 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 12 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 13 | `rules.rolled` | ✅ | rolled=False |
| 13 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=13 |
| 13 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 13 | `universal.location_change.applied` | ✅ | (no change) |
| 13 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 13 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Calloway', 'Nearby', 'Melvin'] |
| 13 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 13 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 13 | `universal.pc.condition_no_dupes` | ✅ | 3 conditions, no dupes |
| 13 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 13 | `universal.momentum.band_delta` | ✅ | (no roll) |

## Turn Metrics

| # | input | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | retries | parse_fail | duration_s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | Walk over to Caron's table and sit down across f… | 1231 | 2661 | 2127 | 2453 | 3311 | 0 | 0 | 23.08 |
| 2 | I slide 500 credits across the table to Caron an… | 1516 | 2931 | — | 2476 | 3601 | 0 | 0 | 21.57 |
| 3 | I find Halden by the town well and offer to carr… | 1637 | 3258 | 2642 | 2527 | 3719 | 0 | 0 | 32.53 |
| 4 | I leave Marrow's Crossing by the east gate and h… | 1705 | 3773 | 2592 | 2488 | 3585 | 0 | 0 | 32.66 |
| 5 | I walk up to the two toughs at the inn door and … | 1639 | 4332 | 2537 | 2637 | 3850 | 0 | 0 | 30.95 |
| 6 | I drop 200 credits on the ground between the tou… | 1643 | 4723 | 2653 | 2772 | 3851 | 0 | 0 | 39.37 |
| 7 | I sit across from Halden at his table, slide the… | 1692 | 4229 | 2589 | 2485 | 3773 | 0 | 0 | 32.32 |
| 8 | I pull out the brass key Halden gave me and try … | 1553 | 4373 | 2442 | 2630 | 3599 | 0 | 0 | 33.78 |
| 9 | I press my ear against the inn's stone wall and … | 1622 | 4703 | 2467 | 2660 | 3659 | 0 | 0 | 29.35 |
| 10 | I approach Matthew Estrada at the bar, grab his … | 1561 | 4995 | 2485 | 2738 | 3623 | 0 | 0 | 30.46 |
| 11 | Matthew's bodyguard draws a knife! I tackle him … | 1654 | 5462 | 2600 | 2635 | 3655 | 0 | 0 | 35.28 |
| 12 | I grab the ledger from my coat and sprint out th… | 1602 | 5866 | 2533 | — | 3520 | 0 | 0 | 37.18 |
| 13 | I find a quiet corner at the dock and wrap my wo… | 1587 | 3921 | 2389 | 2522 | 3336 | 0 | 0 | 30.22 |
|  | TOTALS | 20642 | 55227 | 30056 | 31023 | 47082 | 0 | 0 | 408.77 |

**Total turns:** 13 · **Total duration:** 408.77s · **Avg/turn:** 31.44s
**Total tokens in:** 184,030 · **Total tokens out:** 143,643 · **Total LLM time:** 392.7s
**Total retries:** 0 · **Total parse failures:** 0

