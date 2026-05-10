# Eval Report — `full_cycle`

**Pack:** `eval-pack` · **Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8` · **Temp override:** `None`  
**Started:** 2026-05-10T18:09:13.503916+00:00 · **Finished:** 2026-05-10T18:16:09.303789+00:00  
**Output dir:** `/Users/pwilson/Repos/ccya/evals/runs/20260510T180913Z_2do6ma7m`  
**Compared against:** _(no prior run found)_

## Judge Summary

**Mechanical:** 3/5  
**Narrative:** 4/5  
**Rubric:** `/Users/pwilson/Repos/ccya/evals/rubrics/default.md`
**Judge model:** `mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit`

**Pipeline scores:**
- rules: 4/5
- narrate: 4/5
- extract_scene: 3/5
- extract_state: 3/5
- extract_progress: 3/5

**Trace:** [`full_cycle.trace.md`](full_cycle.trace.md)
**Judge response:** [`full_cycle.judge.md`](full_cycle.judge.md)

## ⚠️  Flagged

### `extraction_retries` — 1 retried extraction stream(s)

- turn 3 `extraction.scene` attempts=2

## Other observations

- **`extract_parse_failures`**: 1 extract parse failure(s) across the run
- turn 3: 1 failure(s)


## Judge Verdict (full)

# Table of Contents
- [Verdict](#verdict)
- [Actionable Issues Surfaced](#actionable-issues-surfaced)
- [Mechanical Design Critique](#mechanical-design-critique)
  - [Pipeline: rules](#pipeline-rules)
  - [Pipeline: narrate](#pipeline-narrate)
  - [Pipeline: extract_scene](#pipeline-extract_scene)
  - [Pipeline: extract_state](#pipeline-extract_state)
  - [Pipeline: extract_progress](#pipeline-extract_progress)
- [Storytelling Design Critique](#storytelling-design-critique)
  - [Criterion: quest_arc_quality](#criterion-quest_arc_quality)
  - [Criterion: rewards_and_consequences](#criterion-rewards_and_consequences)
  - [Criterion: narrative_compellingness](#criterion-narrative_compellingness)
  - [Criterion: npc_development](#criterion-npc_development)
  - [Criterion: world_consistency](#criterion-world_consistency)
  - [Criterion: player_agency](#criterion-player_agency)
  - [Criterion: consequence_persistence](#criterion-consequence_persistence)
  - [Criterion: pacing_and_pressure](#criterion-pacing_and_pressure)
  - [Criterion: momentum_arc](#criterion-momentum_arc)
  - [Criterion: pressure_arc](#criterion-pressure_arc)
  - [Criterion: beat_lifecycle](#criterion-beat_lifecycle)
  - [Criterion: directive_narration_binding](#criterion-directive_narration_binding)
  - [Criterion: stakes_routing](#criterion-stakes_routing)
  - [Criterion: deescalation_mechanics](#criterion-deescalation_mechanics)
- [Prompt Redundancy Analysis](#prompt-redundancy-analysis)
- [Compaction Capabilities Report](#compaction-capabilities-report)
- [Auto-Checker Failures](#auto-checker-failures)
- [Additional Observations](#additional-observations)

---

# Verdict
The engine demonstrates strong mechanical alignment between dice bands and narrative outcomes, with effective pressure and quest lifecycle management. However, critical failures in state extraction (Turn 6 inventory mismatch), quest deduplication (Turn 4), and compaction execution (Turns 7–11) undermine systemic reliability. The most important fix is to harden the state extractor's inventory amount parsing against player-specified sums and implement strict recent-events deduplication in the progress extractor before quest updates are emitted.

# Actionable Issues Surfaced

**Major**
- `[Engine]` **Inventory Amount Mismatch** (Turn 6) — Failure mode: `failed to output key information`. The player explicitly stated "drop 200 credits," but the state extractor emitted `inventory_remove: [{id: credits, amount: 50}]`. The extractor must parse exact amounts from narration or rules stakes when a specific sum is stated, rather than defaulting to a generic or incorrect value.
- `[Engine]` **Compaction Execution Gap** (Turns 7–11, 13) — Failure mode: `wasted tokens`. The trace signals show compaction events firing on non-multiples of 6 (T7, T8, T9, T10, T11, T13) but producing zero bullets. This indicates a logic bug in the compactor trigger or a silent prompt failure. Either align the compactor to fire strictly at `compact_every` intervals, or fix the prompt so it reliably outputs summary bullets when triggered.

**Minor**
- `[Prompting]` **Quest Deduplication Failure** (Turn 4) — Failure mode: `messy logic`. The progress extractor marked `deliver_the_ledger` objective 1 as `done: true` again, despite it being completed in Turn 3. The prompt must explicitly instruct the model to cross-reference `recent_events` and `active_quests` to prevent re-emitting completed objectives.
- `[Consistency]` **Auto-Checker False Positives on Bolded Items** — Failure mode: `bad prompt`. The narrator prompt instructs bolding named inventory items (`**Leather-bound ledger**`, `**Credits**`). The auto-checker flags these as unsanctioned NPCs. Either adjust the checker to ignore bolded inventory/location terms, or refine the narrator prompt to only bold NPC names, not items.

**Trivial**
- `[Prompting]` **Generic Beat Instructions** (Turns 5, 9) — Failure mode: `wasted tokens`. Beats like "The source of the scraping sound emerges" are mechanically sound but narratively vague. Instruct the progress extractor to ground beats in specific named entities or recent events to improve downstream narrative impact.

# Mechanical Design Critique

## Pipeline: rules
### What Went Well
The rules pipeline consistently classifies intents accurately and determines when dice are required. Turn 5 correctly identifies a `persuade` check against toughs, and Turn 11 correctly identifies a `strength` check for tackling. The anti-declare-outcome rule is respected; the engine doesn't let player phrasing dictate success.

### What Went Poorly
Turn 9 classifies "bribe the wall" as a `deceive` check with `required: true`. This is a borderline case; the prompt's anti-declare rule and routine action guidance suggest this should likely be `required: false` or a trivial check, as bribing inanimate architecture has no meaningful consequence. Over-rolling on trivial actions wastes tokens and breaks pacing.

### Prompt Analysis
The rules prompt is well-structured but slightly bloated with directive notes that don't affect the JSON output. The `intent_verb` mapping table is helpful but could be condensed. No major redundancy detected in the rules prompt itself.

### Mechanic Placement
All mechanics (`intent`, `check`, `band`, `directive`) are correctly owned by the rules pipeline. No scope mismatches.

### Issues
- **Over-rolling trivial actions** (Turns 9, 13) — Failure mode: `scope/domain mismatch`. Remediation: Tighten the `check.required` decision rule to explicitly exclude actions directed at inanimate objects or environmental features unless they directly impact a quest or NPC.

### Pipeline Score (1-5)
4

## Pipeline: narrate
### What Went Well
The narrator consistently binds dice bands to prose. Turn 5's `setback` results in the toughs demanding a toll, matching the directive. Turn 11's `partial` results in a successful tackle but a caused scene, perfectly aligning with the "success at a cost" directive. Prose quality is high, adhering to the plain, second-person past-tense style.

### What Went Poorly
Turn 6's narration for a `setback` on deception ("The bribe is rejected... they demand more") is mechanically sound but narratively repetitive of Turn 5's outcome. The narrator could have varied the NPC reaction to show escalation rather than a static refusal. Additionally, the narrator occasionally bolds generic terms (`**Leather-bound ledger**`) which triggers auto-checker noise.

### Prompt Analysis
The narrate prompt contains extensive style guides that are largely redundant with the World Pack Style. The `active scope tail` instructions are clear but could be shortened. The instruction to bold inventory items conflicts with the auto-checker; removing this or clarifying it as "bold only on first mechanical interaction" would help.

### Mechanic Placement
Narration correctly outputs prose and scope. No misplaced mechanics.

### Issues
- **Repetitive NPC reactions to setbacks** (Turns 5, 6) — Failure mode: `messy logic`. Remediation: Instruct the narrator to escalate NPC hostility or introduce new complications on consecutive setbacks, rather than repeating the same refusal pattern.

### Pipeline Score (1-5)
4

## Pipeline: extract_scene
### What Went Well
Scene extraction accurately tracks NPC presence and location changes. Turn 3 correctly identifies `location_change` to `marrows_crossing_streets`. Turn 5 correctly adds `tough_a` and `tough_b` to `present_npcs`. The `npc_update` field is used effectively to track attitude shifts (e.g., Turn 6 toughs becoming hostile).

### What Went Poorly
Turn 3's `npc_add` for `bystanders` is unnecessary ambient noise that clutters the compendium. Turn 8's `npc_add` for `inn_patrons` is similarly low-value. The extractor should prioritize named or interacting NPCs over generic crowd mentions to keep state lean.

### Prompt Analysis
The scene prompt is detailed but could benefit from a stricter `npc_add` threshold. It currently allows ambient presence to be added as compendium entries, which bloats state. Citing Turn 3 and Turn 8 shows this pattern.

### Mechanic Placement
All scene mechanics (`npc_add`, `location_change`, `scene_tags`) are correctly owned by the scene pipeline. No scope mismatches.

### Issues
- **Over-extraction of ambient NPCs** (Turns 3, 8) — Failure mode: `wasted tokens`. Remediation: Add a prompt rule: `Only emit npc_add for named characters or entities that interact with the player or quest. Omit generic crowds or ambient presence.`

### Pipeline Score (1-5)
3

## Pipeline: extract_state
### What Went Well
State extraction correctly handles inventory additions and condition lifecycles. Turn 11 accurately adds `glass_cuts` and `leather_pouch`/`folded_parchment`. Turn 12 correctly removes `bruised_ribs` and adds `bruised_ribs_worsened`, showing good condition tracking.

### What Went Poorly
Turn 6 is a critical failure: the player states "drop 200 credits," but the extractor emits `amount: 50`. This breaks inventory tracking and player trust. Additionally, Turn 13 fails to remove `credits` for the dock boy payment, despite the narration explicitly stating "pressing a few Credits into his palm." This is a missed extraction.

### Prompt Analysis
The state prompt includes good generic item mapping rules, but lacks explicit instructions to parse exact numerical values from player narration when stated. It also doesn't explicitly warn against ignoring explicit spending actions. Citing Turn 6 and Turn 13 highlights this gap.

### Mechanic Placement
All state mechanics (`inventory_add/remove`, `pc_condition_add/remove`) are correctly owned by the state pipeline. No scope mismatches.

### Issues
- **Inventory amount parsing failure** (Turn 6) — Failure mode: `failed to output key information`. Remediation: Instruct the extractor to prioritize explicit numerical values in narration (`"drop 200 credits"`) over generic defaults or assumptions.
- **Missed inventory removal** (Turn 13) — Failure mode: `failed to output key information`. Remediation: Add a prompt rule: `If narration describes spending or giving away currency/items, always emit inventory_remove, even if the amount is vague ("a few").`

### Pipeline Score (1-5)
3

## Pipeline: extract_progress
### What Went Well
Progress extraction correctly handles quest updates and pressure lifecycles. Turn 2 completes `settle_the_debt`. Turn 5 adds `inn_entrance_blockade` pressure. Turn 7 removes `imminent_combat` pressure. The `actions` field consistently provides 4 distinct, quest-weighted choices.

### What Went Poorly
Turn 4 marks `deliver_the_ledger` objective 1 as done again, despite it being completed in Turn 3. This deduplication failure causes redundant state updates. Additionally, Turn 12 marks the quest as `completed` but leaves objectives 2 and 3 as `done: false`. The engine auto-completes quests when all objectives are done, but the extractor shouldn't emit `status: completed` prematurely.

### Prompt Analysis
The progress prompt is comprehensive but lacks a strict deduplication step for quest objectives. It also doesn't explicitly forbid emitting `status: completed` until the engine's auto-completion logic runs. Citing Turn 4 and Turn 12 shows these logic gaps.

### Mechanic Placement
All progress mechanics (`quest_updates`, `scene_pressure_add`, `gm_beat`) are correctly owned by the progress pipeline. No scope mismatches.

### Issues
- **Quest objective deduplication failure** (Turn 4) — Failure mode: `messy logic`. Remediation: Add a prompt rule: `Before emitting quest_updates, check recent_events and active_quests. If an objective is already marked done, do not re-emit it.`
- **Premature quest completion status** (Turn 12) — Failure mode: `schema drift`. Remediation: Instruct the extractor to only mark objectives as done. Let the engine's delta validator handle quest status transitions to `completed`.

### Pipeline Score (1-5)
3

# Storytelling Design Critique

## Criterion: quest_arc_quality
Score: 4
Quests form a clear, compelling arc: debt cleared, ledger accepted, delivery confirmed, then complications arise. Completing `settle_the_debt` in Turns 1-2 feels earned and removes a major tension point, allowing focus on the ledger quest. The progression is logical and maintains player motivation.

## Criterion: rewards_and_consequences
Score: 4
Rolls are consistently rewarded or penalized. Turn 5's `setback` results in a toll demand. Turn 11's `partial` grants items but causes a scene. Momentum moves correctly: `setback` → -1, `success` → +1, `fail` → -1. Conditions are applied for costs (Turn 5 `shaken`, Turn 11 `glass_cuts`). The only flaw is the Turn 6 inventory mismatch, which breaks consequence tracking for that turn.

## Criterion: narrative_compellingness
Score: 4
The story maintains tension through escalating complications: toughs, bodyguard, tavern brawl, escape. Choices matter; failing to escape leads to a trapped state, opening new interaction paths. Prose is vivid and adheres to the plain, sensory style. The narrative never feels static.

## Criterion: npc_development
Score: 4
NPCs evolve meaningfully. Caron shifts from patient creditor to dismissive. Halden moves from relieved merchant to paranoid informant. Matthew remains stoic but reveals tactical awareness. Toughs escalate from extortionists to violent antagonists. Reactions feel grounded in their established roles.

## Criterion: world_consistency
Score: 3
World entities are generally sanctioned, but the auto-checker flags bolded inventory items (`**Leather-bound ledger**`, `**Credits**`) as unsanctioned NPCs. This is a prompt/checker conflict, not a world-building flaw. Otherwise, locations, factions, and items align with the seed state and narration.

## Criterion: player_agency
Score: 4
The engine respects player choices. Failures create new options (brawl → escape → dock) rather than dead-ends. The narrator interprets absurd inputs pragmatically (Turn 9: bribing the wall). Suggested actions are weighted toward quest objectives and present NPCs, supporting meaningful decision-making.

## Criterion: consequence_persistence
Score: 4
Conditions persist correctly: `shaken` and `glass_cuts` carry forward. `bruised_ribs` is properly upgraded to `worsened`. Scene pressures escalate and resolve as expected: `inn_entrance_blockade` → `imminent_combat` → resolved. No conditions or pressures silently disappear without narrative justification.

## Criterion: pacing_and_pressure
Score: 4
Pacing balances high-tension confrontations (Turns 5, 11) with breathing room (Turns 1, 3, 13). Momentum tone aligns with narration: negative momentum correlates with setbacks and traps; positive momentum correlates with successful negotiations and escapes. The arc feels satisfying.

## Criterion: momentum_arc
Score: 4
Momentum plot: T1(0) → T2(0) → T3(0) → T4(0) → T5(-1) → T6(-2) → T7(-1) → T8(0) → T9(-1) → T10(0) → T11(0) → T12(-1) → T13(-1). It reaches meaningful extremes (-2) and correlates with narration tone. The arc has a clear shape: initial stability, descent into trouble, partial recovery, final setback.

## Criterion: pressure_arc
Score: 4
Pressures escalate correctly: `road_toughs_threat` (building) → `inn_entrance_blockade` (immediate) → `imminent_combat` (immediate) → resolved. Urgency levels align with narration stakes. Expired pressures are removed or replaced logically. The pressure system drives the session's dramatic shape effectively.

## Criterion: beat_lifecycle
Score: 3
Beats are generated at a reasonable frequency but sometimes lack specific grounding. Turn 5's `revelation` beat ("Caron mentions the road is hungry") is generic. Turn 9's `pressure` beat ("scraping sound emerges") is vague. Consumption rate is good (beats surface within 1-2 turns), but instruction quality needs tightening to reference specific named entities or recent events.

## Criterion: directive_narration_binding
Score: 4
Narration consistently matches band/directive. `setback` → complication/cost. `partial` → success with consequence. `fail` → outright failure with cost. `success` → clean outcome. No band inversions detected. The binding is strong and reliable.

## Criterion: stakes_routing
Score: 4
Stakes named by rules are mechanically followed. Turn 5's stakes ("toughs may become hostile") materialize as extortion. Turn 11's stakes ("bodyguard recovers quickly") materialize as scene escalation. Conditions and pressures are extracted when stakes are named. No notable routing failures.

## Criterion: deescalation_mechanics
Score: 4
Deescalation works as intended. Turn 7's `success` on charisma resolves `imminent_combat` pressure, and narration pulls back to relief. Turn 8's `success` resolves `road_toughs_threat`. No new pressures are added during deescalation turns. The mechanic successfully provides breathing room.

# Prompt Redundancy Analysis

Reference to `## Prompt Redundancy` signals:
1. **narrate + progress duplication (20 blocks)**: This duplication is largely intentional, as the progress extractor needs `prior_turn_narration` and `recent_events` for context. However, the `recent_events` and `prior_history` blocks are identical across streams, wasting tokens.
2. **narrate + scene duplication (1 block)**: This is the location description, which is correctly fed to both for spatial grounding. Intentional.

**Top 3 dedup opportunities:**
- **`recent_events` block**: Feed a condensed summary to the progress extractor instead of the full list. The scene extractor doesn't need it.
- **`prior_turn_narration`**: The progress extractor receives the full prior turn narration. A 2-sentence outcome summary would suffice for quest/action context, saving ~300 tokens/turn.
- **`active_quests`**: Repeated in both narrate and progress prompts. Move quest context to a dedicated `quest_context` surface that both streams can reference without duplication.

# Compaction Capabilities Report

**Turn 6**: `[OK]` — Produced 3 bullets covering T1-T3. Correctly captured debt settlement, payment, and ledger contract.
**Turn 7**: `[FAIL]` — Compaction event fired but produced 0 bullets. Recent events grew to 4 entries without consolidation.
**Turn 8**: `[FAIL]` — Compaction event fired but produced 0 bullets. Recent events grew to 5 entries.
**Turn 9**: `[FAIL]` — Compaction event fired but produced 0 bullets. Recent events grew to 6 entries.
**Turn 10**: `[FAIL]` — Compaction event fired but produced 0 bullets. Recent events remained at 6 entries.
**Turn 11**: `[FAIL]` — Compaction event fired but produced 0 bullets. Recent events grew to 7 entries.
**Turn 12**: `[OK]` — Produced 6 bullets covering T4-T9. Correctly captured travel, tough encounter, bribe, ledger delivery, key use, and passage investigation.
**Turn 13**: `[FAIL]` — Compaction event fired but produced 0 bullets. Recent events grew to 4 entries.

**Justification**: The compactor only executed correctly at multiples of 6 (T6, T12). The trace signals indicate compaction events firing on other turns but yielding zero output, suggesting a trigger logic bug or prompt failure in the compaction pipeline for non-standard intervals. This results in unbounded `recent_events` growth between T6 and T12.

# Auto-Checker Failures

| Turn | Assertion | Detail | Why it failed | Remediation |
|---|---|---|---|---|
| 1, 2, 3, 4, 5, 7, 8, 9, 10, 11 | `universal.npc_mention.extracted` | Narration mentions names not in npc_add/update or known: ['Instead', 'Crossed', 'Marrow', 'Leather', 'Ignoring', 'Credit', 'Passage', 'Estrada', 'Matthew'] | The narrator prompt instructs bolding named inventory items (`**Leather-bound ledger**`, `**Credits**`) and locations (`**Crossed Keys Inn**`). The auto-checker incorrectly flags these bolded terms as unsanctioned NPCs. This is a prompt/checker schema conflict, not a world-consistency failure. | Adjust the auto-checker to ignore bolded terms that match inventory or location schemas, or refine the narrator prompt to only bold NPC names, not items/locations. |

# Additional Observations

- **Momentum tracking is robust**: The engine correctly applies momentum deltas per band and caps them within `[-3, +3]`. The narrative tone consistently reflects momentum shifts.
- **Pressure lifecycle is well-implemented**: Pressures escalate, persist, and resolve logically. The `urgency` field correctly influences narration stakes.
- **Compaction trigger mismatch**: The trace shows compaction events firing on turns 7, 8, 9, 10, 11, 13, contradicting the `compact_every=6` constant. This suggests the compactor is firing on every turn or a different interval, but only producing bullets at T6/T12. This needs debugging to align with engine constants.
- **State delta validation is silent**: No rejected deltas are logged, indicating the validator is passing all extractions. This is good, but the Turn 6 inventory mismatch slipped through, suggesting the validator doesn't cross-check extracted amounts against player-specified sums.

## Auto-Checker

**133 passed, 20 failed**

| Turn | Assertion | Result | Detail |
|---|---|---|---|
| 1 | `rules.rolled` | ✅ | rolled=False |
| 1 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 1 | `universal.pending_gm_beat.consumed` | ✅ | (first turn) |
| 1 | `universal.location_change.applied` | ✅ | (no change) |
| 1 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 1 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Instead'] |
| 1 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 1 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 1 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 1 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 1 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 2 | `rules.rolled` | ❌ | rolled=False |
| 2 | `extract.state.inventory_remove` | ❌ | inventory_remove[credits] not found |
| 2 | `extract.progress.quest_updates` | ✅ | quest_updates[settle_the_debt] found |
| 2 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 2 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 2 | `universal.location_change.applied` | ✅ | (no change) |
| 2 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 2 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Instead'] |
| 2 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 2 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 2 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 2 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 2 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 3 | `rules.rolled` | ❌ | rolled=False |
| 3 | `extract.progress.quest_updates` | ✅ | quest_updates[deliver_the_ledger] found |
| 3 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=3 |
| 3 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 3 | `universal.location_change.applied` | ✅ | marrows_crossing -> marrows_crossing_streets |
| 3 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 3 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed', 'Crossing', 'Marrow'] |
| 3 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 3 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 3 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 3 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 3 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 4 | `rules.rolled` | ✅ | rolled=False |
| 4 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=4 |
| 4 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 4 | `universal.location_change.applied` | ✅ | marrows_crossing_streets -> merchant_road_east |
| 4 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 4 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossing', 'Leather', 'Marrow'] |
| 4 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 4 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 4 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 4 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 4 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 5 | `rules.rolled` | ✅ | rolled=True |
| 5 | `extract.scene.scene_tags` | ❌ | scene_tags[combat] not found |
| 5 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=5 |
| 5 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 5 | `universal.location_change.applied` | ✅ | merchant_road_east -> crossed_keys_inn_exterior |
| 5 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 5 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 5 | `universal.recent_events.ring_bounded` | ✅ | 6 entries |
| 5 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 5 | `universal.pc.condition_no_dupes` | ✅ | 3 conditions, no dupes |
| 5 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 5 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 6 | `rules.rolled` | ✅ | rolled=True |
| 6 | `extract.state.inventory_remove` | ❌ | inventory_remove[credits] amount=50 |
| 6 | `extract.progress.quest_updates` | ❌ | quest_updates[clear_the_road_toughs] not found |
| 6 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 6 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 6 | `universal.location_change.applied` | ✅ | (no change) |
| 6 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 6 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 6 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 6 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 6 | `universal.pc.condition_no_dupes` | ✅ | 3 conditions, no dupes |
| 6 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 6 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 7 | `extract.progress.quest_updates` | ✅ | quest_updates[deliver_the_ledger] found |
| 7 | `extract.progress.quest_status` | ❌ | quest[deliver_the_ledger].status='active' (expected 'completed') |
| 7 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=7 |
| 7 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 7 | `universal.location_change.applied` | ✅ | crossed_keys_inn_exterior -> crossed_keys_inn_interior |
| 7 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 7 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Leather', 'Crossed'] |
| 7 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 7 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 7 | `universal.pc.condition_no_dupes` | ✅ | 3 conditions, no dupes |
| 7 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 7 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 8 | `rules.rolled` | ✅ | rolled=True |
| 8 | `extract.state.inventory_remove` | ❌ | inventory_remove[brass_key] not found |
| 8 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=8 |
| 8 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 8 | `universal.location_change.applied` | ✅ | crossed_keys_inn_interior -> crossed_keys_inn_back_passage |
| 8 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 8 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Ignoring'] |
| 8 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 8 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 8 | `universal.pc.condition_no_dupes` | ✅ | 3 conditions, no dupes |
| 8 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 8 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 9 | `rules.rolled` | ✅ | rolled=True |
| 9 | `extract.scene.scene_tags` | ❌ | scene_tags[social] not found |
| 9 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=9 |
| 9 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 9 | `universal.location_change.applied` | ✅ | (no change) |
| 9 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 9 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed', 'Credit', 'Passage'] |
| 9 | `universal.recent_events.ring_bounded` | ✅ | 6 entries |
| 9 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 9 | `universal.pc.condition_no_dupes` | ✅ | 3 conditions, no dupes |
| 9 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 9 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 10 | `rules.rolled` | ✅ | rolled=True |
| 10 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 10 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 10 | `universal.location_change.applied` | ✅ | crossed_keys_inn_back_passage -> crossed_keys_inn_common_room |
| 10 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 10 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Estrada', 'Matthew', 'Passage'] |
| 10 | `universal.recent_events.ring_bounded` | ✅ | 6 entries |
| 10 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 10 | `universal.pc.condition_no_dupes` | ✅ | 3 conditions, no dupes |
| 10 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 10 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 11 | `rules.rolled` | ✅ | rolled=True |
| 11 | `extract.scene.scene_tags` | ✅ | scene_tags[combat] found |
| 11 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=11 |
| 11 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 11 | `universal.location_change.applied` | ✅ | (no change) |
| 11 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 11 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Estrada', 'Matthew', 'Instead'] |
| 11 | `universal.recent_events.ring_bounded` | ✅ | 7 entries |
| 11 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 11 | `universal.pc.condition_no_dupes` | ✅ | 4 conditions, no dupes |
| 11 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 11 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 12 | `rules.rolled` | ❌ | rolled=True |
| 12 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=12 |
| 12 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 12 | `universal.location_change.applied` | ✅ | (no change) |
| 12 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 12 | `universal.npc_mention.extracted` | ✅ | 4 candidates skipped (likely locations/items, not NPCs) |
| 12 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 12 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 12 | `universal.pc.condition_no_dupes` | ✅ | 4 conditions, no dupes |
| 12 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 12 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 13 | `rules.rolled` | ✅ | rolled=False |
| 13 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=13 |
| 13 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 13 | `universal.location_change.applied` | ✅ | crossed_keys_inn_common_room -> river_docks_alcove |
| 13 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 13 | `universal.npc_mention.extracted` | ✅ | 6 candidates skipped (likely locations/items, not NPCs) |
| 13 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 13 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 13 | `universal.pc.condition_no_dupes` | ✅ | 4 conditions, no dupes |
| 13 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 13 | `universal.momentum.band_delta` | ✅ | (no roll) |

## Turn Metrics

| # | input | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | retries | parse_fail | duration_s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | Walk over to Caron's table and sit down across f… | 1231 | 2489 | 2115 | 2156 | 3220 | 0 | 0 | 29.71 |
| 2 | I slide 500 credits across the table to Caron an… | 1522 | 2775 | — | — | 3448 | 0 | 0 | 17.91 |
| 3 | I find Halden by the town well and offer to carr… | 1585 | 3120 | 2568 | 2243 | 3567 | 1 | 1 | 34.89 |
| 4 | I leave Marrow's Crossing by the east gate and h… | 1609 | 3447 | 2409 | 2118 | 3263 | 0 | 0 | 28.22 |
| 5 | I walk up to the two toughs at the inn door and … | 1546 | 3860 | 2478 | 2503 | 3663 | 0 | 0 | 32.50 |
| 6 | I drop 200 credits on the ground between the tou… | 1686 | 4467 | 2616 | 2479 | 3804 | 0 | 0 | 36.57 |
| 7 | I sit across from Halden at his table, slide the… | 1642 | 3937 | 2646 | 2349 | 3568 | 0 | 0 | 32.73 |
| 8 | I pull out the brass key Halden gave me and try … | 1706 | 4348 | 2579 | 2235 | 3500 | 0 | 0 | 30.58 |
| 9 | I press my ear against the inn's stone wall and … | 1625 | 4725 | 2437 | 2206 | 3297 | 0 | 0 | 29.27 |
| 10 | I approach Matthew Estrada at the bar, grab his … | 1525 | 5100 | 2449 | 2322 | 3583 | 0 | 0 | 28.61 |
| 11 | Matthew's bodyguard draws a knife! I tackle him … | 1591 | 5390 | 2576 | 2406 | 3676 | 0 | 0 | 35.69 |
| 12 | I grab the ledger from my coat and sprint out th… | 1652 | 5729 | 2654 | 2527 | 3814 | 0 | 0 | 43.16 |
| 13 | I find a quiet corner at the dock and wrap my wo… | 1653 | 3964 | 2701 | 2488 | 3662 | 0 | 0 | 35.89 |
|  | TOTALS | 20573 | 53351 | 30228 | 28032 | 46065 | 1 | 1 | 415.72 |

**Total turns:** 13 · **Total duration:** 415.72s · **Avg/turn:** 31.98s
**Total tokens in:** 178,249 · **Total tokens out:** 140,275 · **Total LLM time:** 399.5s
**Total retries:** 1 · **Total parse failures:** 1

