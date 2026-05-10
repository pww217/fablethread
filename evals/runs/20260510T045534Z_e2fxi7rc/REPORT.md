# Eval Report — `full_cycle`

**Pack:** `eval-pack` · **Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8` · **Temp override:** `None`  
**Started:** 2026-05-10T04:55:34.630753+00:00 · **Finished:** 2026-05-10T05:02:13.611504+00:00  
**Output dir:** `/Users/pwilson/Repos/ccya/evals/runs/20260510T045534Z_e2fxi7rc`  
**Compared against:** `/Users/pwilson/Repos/ccya/evals/runs/20260510T043601Z_trrtunn7/artifacts`

## Judge Summary

**Mechanical:** 3/5  
**Narrative:** 3/5  
**Rubric:** `/Users/pwilson/Repos/ccya/evals/rubrics/default.md`
**Judge model:** `mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit`

**Pipeline scores:**
- rules: 4/5
- narrate: 2/5
- extract_scene: 3/5
- extract_state: 3/5
- extract_progress: 3/5

**Trace:** [`full_cycle.trace.md`](full_cycle.trace.md)
**Judge response:** [`full_cycle.judge.md`](full_cycle.judge.md)

## ⚠️  Flagged

### `rejected_deltas` — 2 rejected delta(s) across the run

- turn 7: 1 rejected
- turn 13: 1 rejected

## Other observations

- **`runner_errors`**: 2 turn(s) errored
- turn 7: engine_errors: [{"trace_id": "6ae19b2c", "message": "Delta validation failed (1 rejection(s))."}]
- turn 13: engine_errors: [{"trace_id": "d10c5891", "message": "Delta validation failed (1 rejection(s))."}]


## Judge Verdict (full)

# Table of Contents
- [Mechanical Design Critique](#mechanical-design-critique)
  - [Pipeline: rules](#pipeline-rules)
  - [Pipeline: narrate](#pipeline-narrate)
  - [Pipeline: extract_scene](#pipeline-extract_scene)
  - [Pipeline: extract_state](#pipeline-extract_state)
  - [Pipeline: extract_progress](#pipeline-extract_progress)
- [Storytelling Design Critique](#storytelling-design-critique)
- [Prompt Redundancy Analysis](#prompt-redundancy-analysis)
- [Compaction Capabilities Report](#compaction-capabilities-report)
- [Auto-Checker Failures](#auto-checker-failures)
- [Additional Observations](#additional-observations)
- [Verdict](#verdict)
- [Actionable Issues and Remediations](#actionable-issues-and-remediations)

---

# Mechanical Design Critique

## Pipeline: rules
### What Went Well
The rules pipeline consistently classifies player intent accurately across varied inputs. Turn 5 correctly identifies a `persuade` check against toughs, and Turn 11 correctly classifies a `strength` tackle. The dice resolution logic in Python handles condition modifiers properly (e.g., Turn 12 applies `-1` for `wounded_ribs`/`exhausted` to the dexterity escape roll). The anti-declare-outcome rule is respected; the engine never lets player prose dictate success, forcing checks even for seemingly trivial actions like Turn 8's lockpicking.

### What Went Poorly
Turn 7 exhibits a critical context slip. The player input explicitly targets Halden (`"I sit across from Halden at his table..."`), but the rules extractor hallucinates a `persuade` check against Halden despite Halden not being in the scene. More importantly, the narrator completely ignores this input in the subsequent turn, describing Turn 6's aftermath instead. While this is primarily a narrate failure, the rules pipeline fed a stale or misaligned `rules_outcome` into the narrator, compounding the break. Additionally, Turn 3 classifies a negotiation for a delivery contract as `negotiate` with no roll, which is correct, but the stakes field remains empty despite the narrative warning about "vultures" and "books like this one." Stakes should reflect the explicit danger mentioned in the narration to inform future pressure generation.

### Prompt Analysis
The rules system prompt is well-structured but lacks a strong directive to cross-reference `scene.present_npcs` before classifying targets. Turn 7's hallucination could be prevented by adding a mandatory check: `If target is not in scene.present_npcs or known_characters, set check.required=false and flag as untargetable.` The prompt also needs to enforce populating `stakes` when the narration or world state implies explicit danger, rather than leaving it empty.

### Mechanic Placement
Intent classification correctly lives in rules. Dice resolution correctly lives in Python. No misplaced mechanics detected.

### Issues
- **<Context slip on Turn 7>** (Turns: 7) — Failure mode: `failed to input key information`. The extractor classifies a check against an absent NPC. Remediation: Add a scene-presence validation step in the rules pipeline that rejects checks against NPCs not in `present_npcs` or `known_characters`.
- **<Empty stakes on Turn 3>** (Turns: 3) — Failure mode: `failed to output key information`. Remediation: Instruct the rules LLM to extract explicit threats from the narration or world state into the `stakes` field to seed future pressure.

### Pipeline Score (1-5)
4

## Pipeline: narrate
### What Went Well
The prose quality is consistently strong, adhering to the `eval-pack` style guide. Turn 6's narration of the failed bribe effectively conveys the `fail` band through visceral description ("white-hot flash of agony," "spits, stepping forward"). Turn 8's stealth escape uses spatial clarity well ("secondary, smaller keyhole tucked into the side of the doorframe"). The narrator correctly consumes `deescalate` flags and `rules_outcome` directives, aligning prose weight with mechanical outcomes.

### What Went Poorly
Turn 7 is a catastrophic narrative break. The player input is completely ignored, and the narrator outputs prose describing the immediate aftermath of Turn 6's violence instead of processing Turn 7's input. This creates a disjointed experience where the player's action vanishes. Turn 13 also shows a system error marker (`*That action didn't resolve as expected...*`), indicating a fallback or retry loop that leaked into the trace, further degrading immersion. The narrator also occasionally bolds location names or items as if they were NPCs (e.g., Turn 2 bolds `**Credits**`), which confuses downstream extractors.

### Prompt Analysis
The narrate system prompt is bloated with overlapping style rules. The `Active scope tail` section is correctly placed but could be tightened. The prompt lacks a strict instruction to validate player input against `scene.present_npcs` and `location` before generating prose. The bolding rule for items/NPCs is ambiguous; it should explicitly forbid bolding location names or generic items to prevent auto-checker false positives.

### Mechanic Placement
Narration correctly lives in Step 1. The `<scope>` tail correctly gates extractors. No misplaced mechanics.

### Issues
- **<Complete input ignore on Turn 7>** (Turns: 7) — Failure mode: `bad prompt`. The narrator failed to process the user input, outputting stale context. Remediation: Add a pre-narration validation step that checks if the input references absent NPCs/locations and either adapts the scene or prompts the player for clarification instead of hallucinating a response.
- **<Incorrect bolding of items/locations>** (Turns: 2, 3, 5) — Failure mode: `schema drift`. Narrator bolds `**Credits**` and location names, triggering auto-checker failures. Remediation: Explicitly forbid bolding location names and generic currency in the markdown rules.

### Pipeline Score (1-5)
2

## Pipeline: extract_scene
### What Went Well
The scene extractor reliably tracks location changes, NPC presence, and scene tags. Turn 5 correctly identifies the location shift to `crossed_keys_inn` and updates NPC notes for the toughs. Turn 8 accurately removes NPCs from the scene when the player escapes through the service hatch. The compendium pre-check rule is generally followed, preventing duplicate NPC additions.

### What Went Poorly
Turn 2 exhibits a severe schema drift: the extractor emits `scene_pressure_remove: ["settle_the_debt"]`. `settle_the_debt` is a quest ID, not a pressure ID. This indicates the extractor is confusing quest completion with pressure resolution. Turn 3 adds `road_vultures_threat` correctly, but Turn 5 removes it prematurely simply because the player succeeded on a charisma check, without narration explicitly stating the threat was neutralized. The de-escalation rule should require explicit narrative confirmation of threat resolution, not just a successful roll.

### Prompt Analysis
The scene extract prompt needs stricter validation for pressure IDs. It should cross-reference `scene_pressure` keys before emitting removals. The de-escalation rule is too loose; it should mandate that `scene_pressure_remove` only fires when the narration explicitly states the threat is gone, not just when the player succeeds on a check.

### Mechanic Placement
`gm_beat` generation correctly lives in scene extract. Pressure lifecycle correctly lives here. No misplaced mechanics.

### Issues
- **<Quest ID used as Pressure ID on Turn 2>** (Turns: 2) — Failure mode: `schema drift`. Remediation: Add a validation step that checks `scene_pressure_remove` IDs against the active `scene_pressure` list before emitting.
- **<Premature pressure removal on Turn 5>** (Turns: 5) — Failure mode: `messy logic`. Remediation: Require explicit narrative confirmation of threat neutralization for `scene_pressure_remove`.

### Pipeline Score (1-5)
3

## Pipeline: extract_state
### What Went Well
The state extractor accurately handles inventory deltas and condition lifecycles. Turn 6 correctly replaces `bruised_ribs` with `wounded_ribs` following a physical blow. Turn 8 correctly identifies the service corridor escape without inventing inventory changes. The generic item mapping rule is present but inconsistently applied.

### What Went Poorly
Turn 7 and Turn 13 both fail to apply inventory removals because the narrator uses "iron coins" while the inventory tracks `credits`. The extractor emits `iron_coins`, which is rejected by the validator. The prompt's generic item mapping rule ("map to closest matching ID") is ignored by the LLM. Turn 13 also fails to remove the `strained_ribs` condition despite narration stating the player wrapped their wounds to stave off pain, showing a missed condition resolution opportunity.

### Prompt Analysis
The generic item mapping rule is buried in the prompt and lacks a strong directive to fallback to known currency IDs. It should be elevated to a hard constraint: `If narration mentions currency, ALWAYS map to existing currency ID in inventory. Never invent new currency IDs.` The condition removal rule should also be strengthened to trigger on explicit self-care narration.

### Mechanic Placement
Inventory and condition extraction correctly live in state extract. No misplaced mechanics.

### Issues
- **<Generic currency mapping failure on Turn 7 & 13>** (Turns: 7, 13) — Failure mode: `failed to output key information`. Remediation: Hardcode currency mapping in the prompt: `If narration mentions coins/money, map to existing currency ID. Emit inventory_remove for credits.`
- **<Missed condition removal on Turn 13>** (Turns: 13) — Failure mode: `failed to input key information`. Remediation: Instruct extractor to remove conditions when narration describes explicit self-treatment or healing.

### Pipeline Score (1-5)
3

## Pipeline: extract_progress
### What Went Well
The progress extractor correctly handles quest objective completion and recent event logging. Turn 1 marks objective 1 of `settle_the_debt` as done. Turn 3 correctly advances `deliver_the_ledger`. Turn 6 logs the failed bribe as a recent event. The action suggestions are generally relevant to the current scene and quest state.

### What Went Poorly
Turn 4 exhibits a logic bug: objective 1 of `deliver_the_ledger` is reverted to `done: false` despite being completed in Turn 3. This suggests a state merge or extraction regression. Turn 3 completes objective 2 (`Carry the ledger to the merchant Halden at the Crossed Keys Inn`) prematurely; the player is still at the well, not the inn. The "Contact and meet" objective rule is misapplied here. Turn 7 extracts no quest updates or recent events, leaving a mechanical gap.

### Prompt Analysis
The progress extract prompt needs stricter validation for objective completion. It should cross-reference the player's actual location and narration before marking objectives done. The "Contact and meet" rule should be scoped to explicit dialogue or interaction, not just proximity. Turn 4's regression suggests the extractor is receiving stale quest state or misaligning indices.

### Mechanic Placement
Quest updates correctly live in progress extract. Recent events correctly live here. No misplaced mechanics.

### Issues
- **<Premature objective completion on Turn 3>** (Turns: 3) — Failure mode: `scope/domain mismatch`. Remediation: Tie objective completion to explicit narration of arrival/delivery, not just contract acceptance.
- **<Objective regression on Turn 4>** (Turns: 4) — Failure mode: `messy logic`. Remediation: Add a state-diff check to ensure completed objectives are not reverted to false.
- **<Empty extraction on Turn 7>** (Turns: 7) — Failure mode: `failed to output key information`. Remediation: Ensure progress extractor runs even when narrator fails, to capture mechanical consequences of the input.

### Pipeline Score (1-5)
3

---

# Storytelling Design Critique

### quest_arc_quality
Score: 3
Quests form a coherent short arc: debt cleared, ledger accepted, delivery complicated by violence. Turn 1 completes the debt arc satisfyingly. However, Turn 7's narrative break derails the ledger delivery arc, leaving it stalled for 10 turns by the end. The engine handles quest progression well mechanically, but the pacing suffers from the Turn 7 slip.

### rewards_and_consequences
Score: 4
Rolls are generally honored. Turn 5's success defuses the toughs. Turn 6's fail correctly inflicts `wounded_ribs` and aggression. Turn 8's success grants escape. Turn 12's setback correctly adds `strained_ribs` and pursuers. Momentum moves correctly per band. Conditions are applied and replaced logically. The only miss is Turn 7, where no consequences are extracted due to the narrator failure.

### narrative_compellingness
Score: 3
Prose is strong and immersive during functional turns. Turn 6 and Turn 8 are particularly tense and well-paced. Turn 7's complete disconnect from player input severely damages compulsion. Turn 13's fallback marker also breaks immersion. Overall, the fiction is compelling when the pipeline holds together.

### npc_development
Score: 4
NPCs evolve meaningfully. Caron transitions from creditor to indifferent debtor. Halden shifts from nervous merchant to absent quest-giver. Matthew Estrada and Daniel Vane are introduced with distinct physical descriptors and behaviors, escalating tension naturally. Toughs react dynamically to player actions.

### world_consistency
Score: 4
World entities are generally sanctioned. The auto-checker flags some known names/locations, but these are false positives. Locations shift logically (tavern -> outskirts -> inn -> corridor -> docks). Inventory tracking is mostly accurate. No unsanctioned NPCs or items appear.

### player_agency
Score: 3
Player choices generally drive the scene. Turn 5's persuasion succeeds, Turn 8's stealth succeeds. Turn 7 is a major failure where agency is ignored. Turn 13's note-writing is narrated but not mechanically tracked, slightly reducing agency impact.

### consequence_persistence
Score: 4
Conditions persist correctly. `wounded_ribs` -> `strained_ribs` tracks injury escalation. Scene pressures escalate from `building` to `immediate` appropriately. Turn 6's aggression pressure correctly influences Turn 7's narration (even though Turn 7 input was ignored, the pressure state was valid).

### pacing_and_pressure
Score: 4
Pressure mechanics work well. `road_vultures_threat` builds tension, then resolves. `toughs_aggression` escalates to `immediate` after the failed bribe. The escape to the docks introduces `purposeful_pursuit`, maintaining stakes. Narrative pacing balances action and breathing room effectively.

### momentum_arc
Score: 3
Momentum plot: T1(0) -> T2(0) -> T3(0) -> T4(0) -> T5(+1) -> T6(0) -> T7(0) -> T8(0) -> T9(0) -> T10(+1) -> T11(0) -> T12(-1) -> T13(-1). The arc is somewhat flat initially, then oscillates during the tavern escape. It lacks a clear rising peak, but reflects the chaotic, reactive nature of the session. A more deliberate momentum curve would enhance dramatic shape.

---

# Prompt Redundancy Analysis

The Deterministic Signals report identifies two main overlap pairs:
1. **narrate + progress**: Recent Events list is duplicated. This is intentional design, as progress needs recent events to deduplicate and advance quests. However, it wastes ~150 tokens per turn.
2. **narrate + scene**: Location description is duplicated. This is also intentional, as scene needs location context for tagline and pressure generation. Wastes ~80 tokens per turn.

**Top 3 dedup opportunities:**
- **Recent Events duplication**: Pass a condensed 3-bullet summary to progress instead of the full list.
- **Location description duplication**: Pass only `location.id` and `location.name` to scene; let scene extract generate taglines from narration.
- **PC bio/stats duplication**: The full PC bio and stats are repeated in every turn's prompts. Pass a condensed `pc_summary` surface instead.

---

# Compaction Capabilities Report

**Compaction at Turn 6:**
- `bullet_named_npcs`: [OK] Caron mentioned.
- `bullet_location`: [OK] Crossed Keys Inn.
- `bullet_quest_outcomes`: [FAIL] `settle_the_debt` completed at T2, but compaction did not close it or note completion.
- `bullet_key_items`: [OK] Credits spent.
- `bullet_conditions`: [NA] No condition changes in T1-3.
- `sanitize_quest_close`: [FAIL] Quest completed at T2 remains active in compaction output.
- `sanitize_pressure`: [FAIL] No pressures active, but rule not applied.
- `sanitize_condition`: [NA]

**Compaction at Turn 12:**
- `bullet_named_npcs`: [OK] Toughs, Halden mentioned.
- `bullet_location`: [OK] River Outskirts.
- `bullet_quest_outcomes`: [OK] Ledger delivery stalled, debt cleared noted.
- `bullet_key_items`: [OK] Ledger carried.
- `bullet_conditions`: [OK] Ribs aggravated.
- `sanitize_quest_close`: [FAIL] `settle_the_debt` still not closed in compaction sanitization.
- `sanitize_pressure`: [FAIL] `tavern_brawl_chaos` removed, but sanitization record shows `(none recorded)`.
- `sanitize_condition`: [FAIL] `wounded_ribs` replaced, but compaction didn't record removal.

**Overall Compaction Verdict:** The compactor successfully generates narrative bullets but completely fails to apply sanitization deltas (`quest_close`, `pressure_remove`, `condition_remove`, `recent_events_compact`). This is a critical mechanical failure. The compactor fires but acts only as a logger, not a state cleaner.

---

# Auto-Checker Failures

| Turn | Assertion | Detail | Why it failed | Remediation |
|---|---|---|---|---|
| 1 | `universal.npc_mention.extracted` | 'Crossed' | False positive. Auto-checker flags location names as NPCs. Narration mentions "Crossed Keys". | Tune auto-checker to exclude known location IDs from NPC validation. |
| 2 | `universal.npc_mention.extracted` | 'Credits' | False positive. Auto-checker flags item names. Narration bolds `**Credits**`. | Exclude known inventory IDs from NPC validation. Fix narrator bolding rules. |
| 3 | `universal.npc_mention.extracted` | 'Marrow', 'Crossing', 'Crossed' | False positive. Location names flagged. | Same as above. |
| 5 | `universal.npc_mention.extracted` | 'Crossed' | False positive. Location name. | Same as above. |
| 9 | `universal.npc_mention.extracted` | 'However' | False positive. Auto-checker regex error on common words. | Fix auto-checker regex to ignore non-proper nouns. |
| 11 | `universal.npc_mention.extracted` | 'Matthew', 'Daniel', 'Estrada' | False positive. Known compendium NPCs. Auto-checker fails to match them. | Update auto-checker known list matching to include compendium names. |

---

# Additional Observations

1. **Turn 7 System Error**: The trace shows `*That action didn't resolve as expected. Trace ...*` in Turn 13, but Turn 7's narrator output is completely disconnected from input. This suggests a silent retry or context buffer overflow that leaked into Turn 7's narration. The engine should catch this earlier.
2. **Condition ID Normalization**: Turn 6 replaces `bruised_ribs` with `wounded_ribs`. Turn 12 replaces `wounded_ribs` with `strained_ribs`. This is good lifecycle management, but Turn 13's narrator describes wrapping wounds to stave off pain, yet the state extractor doesn't remove `strained_ribs`. The engine should trigger condition removal on explicit self-care narration.
3. **Momentum Oscillation**: Momentum barely moves until Turn 5, then oscillates. The engine's momentum delta config is correct, but the narrative doesn't consistently reward success or punish failure with momentum shifts until later turns.

---

# Verdict

The engine demonstrates strong mechanical foundations in dice resolution, condition tracking, and scene extraction, but suffers from critical pipeline breaks. Turn 7's narrator completely ignores player input, creating a major immersion break. The compactor fires but fails to apply sanitization deltas, leaving stale quests and pressures in state. Auto-checker failures are mostly false positives on known entities. The most important fix is to harden the narrator's input validation and repair the compactor's sanitization pipeline to ensure state cleanliness.

---

# Actionable Issues and Remediations

### Major
- **[Engine] Turn 7 Narrator Input Ignition** — The narrator outputs Turn 6's aftermath instead of processing Turn 7 input. *Remediation*: Add a pre-narration validation step that checks if the input references absent NPCs/locations. If absent, adapt the scene or prompt for clarification instead of hallucinating.
- **[Engine] Compactor Sanitization Failure** — Compaction fires at T6 and T12 but records `(none recorded)` for all sanitization actions. Quests are not closed, pressures not removed. *Remediation*: Debug the compactor's delta application step. Ensure `sanitize_quest_close`, `sanitize_pressure`, and `sanitize_condition` actually emit and apply deltas to state.
- **[Prompting] Generic Currency Mapping** — State extractor emits `iron_coins` instead of mapping to `credits`, causing rejection. *Remediation*: Elevate the generic item mapping rule to a hard constraint in the state extract prompt: `If narration mentions currency, ALWAYS map to existing currency ID. Never invent new currency IDs.`

### Minor
- **[Consistency] Premature Objective Completion** — Turn 3 marks objective 2 of `deliver_the_ledger` as done despite player not being at the inn. *Remediation*: Tie objective completion to explicit narration of arrival/delivery, not just contract acceptance.
- **[Prompting] Scene Pressure ID Validation** — Turn 2 removes pressure using a quest ID. *Remediation*: Add a validation step in scene extract that checks `scene_pressure_remove` IDs against the active `scene_pressure` list before emitting.
- **[Prompting] Auto-Checker False Positives** — Auto-checker flags known locations/items as NPCs. *Remediation*: Tune auto-checker to exclude known location IDs and inventory IDs from NPC validation.

### Trivial
- **[Prompting] Redundant Context Blocks** — Recent Events and location descriptions are duplicated across narrate/scene/progress prompts. *Remediation*: Pass condensed summaries to extractors to save tokens.
- **[Engine] Condition Removal on Self-Care** — Turn 13 narrator describes wrapping wounds, but state extractor doesn't remove `strained_ribs`. *Remediation*: Instruct state extractor to remove conditions when narration describes explicit self-treatment or healing.

## Auto-Checker

**137 passed, 16 failed**

| Turn | Assertion | Result | Detail |
|---|---|---|---|
| 1 | `rules.rolled` | ✅ | rolled=False |
| 1 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 1 | `universal.pending_gm_beat.consumed` | ✅ | (first turn) |
| 1 | `universal.location_change.applied` | ✅ | (no change) |
| 1 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 1 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
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
| 3 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=3 |
| 3 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 3 | `universal.location_change.applied` | ✅ | (no change) |
| 3 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 3 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Marrow', 'Crossing', 'Crossed'] |
| 3 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 3 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 3 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 3 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 3 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 4 | `rules.rolled` | ✅ | rolled=False |
| 4 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=4 |
| 4 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 4 | `universal.location_change.applied` | ✅ | marrows_crossing -> eastern_outskirts |
| 4 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 4 | `universal.npc_mention.extracted` | ✅ | 4 candidates skipped (likely locations/items, not NPCs) |
| 4 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 4 | `universal.scene.npc_cap` | ✅ | 0 NPCs |
| 4 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 4 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 4 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 5 | `rules.rolled` | ✅ | rolled=True |
| 5 | `extract.scene.scene_tags` | ❌ | scene_tags[combat] not found |
| 5 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 5 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 5 | `universal.location_change.applied` | ✅ | eastern_outskirts -> crossed_keys_inn |
| 5 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 5 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Crossed'] |
| 5 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 5 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 5 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 5 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 5 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 6 | `rules.rolled` | ✅ | rolled=True |
| 6 | `extract.state.inventory_remove` | ❌ | inventory_remove[credits] not found |
| 6 | `extract.progress.quest_updates` | ❌ | quest_updates[clear_the_road_toughs] not found |
| 6 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=6 |
| 6 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 6 | `universal.location_change.applied` | ✅ | (no change) |
| 6 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 6 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 6 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 6 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 6 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 6 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 6 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 7 | `extract.progress.quest_updates` | ❌ | quest_updates[deliver_the_ledger] not found |
| 7 | `extract.progress.quest_status` | ❌ | quest[deliver_the_ledger] not found in quest_updates |
| 7 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 7 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 7 | `universal.location_change.applied` | ✅ | (no change) |
| 7 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 7 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 7 | `universal.recent_events.ring_bounded` | ✅ | 3 entries |
| 7 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 7 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 7 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 7 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 8 | `rules.rolled` | ✅ | rolled=True |
| 8 | `extract.state.inventory_remove` | ❌ | inventory_remove[brass_key] not found |
| 8 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=8 |
| 8 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 8 | `universal.location_change.applied` | ✅ | crossed_keys_inn -> crossed_keys_service_corridor |
| 8 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 8 | `universal.npc_mention.extracted` | ✅ | no missing NPC names detected |
| 8 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 8 | `universal.scene.npc_cap` | ✅ | 0 NPCs |
| 8 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 8 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 8 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 9 | `rules.rolled` | ✅ | rolled=True |
| 9 | `extract.scene.scene_tags` | ❌ | scene_tags[social] not found |
| 9 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=9 |
| 9 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 9 | `universal.location_change.applied` | ✅ | (no change) |
| 9 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 9 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['However'] |
| 9 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 9 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 9 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 9 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 9 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 10 | `rules.rolled` | ✅ | rolled=True |
| 10 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=10 |
| 10 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 10 | `universal.location_change.applied` | ✅ | crossed_keys_service_corridor -> crossed_keys_common_room |
| 10 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 10 | `universal.npc_mention.extracted` | ✅ | 4 candidates skipped (likely locations/items, not NPCs) |
| 10 | `universal.recent_events.ring_bounded` | ✅ | 6 entries |
| 10 | `universal.scene.npc_cap` | ✅ | 1 NPCs |
| 10 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 10 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 10 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 11 | `rules.rolled` | ✅ | rolled=True |
| 11 | `extract.scene.scene_tags` | ✅ | scene_tags[combat] found |
| 11 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=11 |
| 11 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 11 | `universal.location_change.applied` | ✅ | (no change) |
| 11 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 11 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Matthew', 'Daniel', 'Estrada'] |
| 11 | `universal.recent_events.ring_bounded` | ✅ | 7 entries |
| 11 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 11 | `universal.pc.condition_no_dupes` | ✅ | 3 conditions, no dupes |
| 11 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 11 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 12 | `rules.rolled` | ❌ | rolled=True |
| 12 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=12 |
| 12 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 12 | `universal.location_change.applied` | ✅ | crossed_keys_common_room -> river_outskirts |
| 12 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 12 | `universal.npc_mention.extracted` | ✅ | 4 candidates skipped (likely locations/items, not NPCs) |
| 12 | `universal.recent_events.ring_bounded` | ✅ | 2 entries |
| 12 | `universal.scene.npc_cap` | ✅ | 0 NPCs |
| 12 | `universal.pc.condition_no_dupes` | ✅ | 3 conditions, no dupes |
| 12 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 12 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 13 | `rules.rolled` | ✅ | rolled=False |
| 13 | `universal.recent_events_add.turn_stamped` | ✅ | (no adds) |
| 13 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 13 | `universal.location_change.applied` | ✅ | (no change) |
| 13 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 13 | `universal.npc_mention.extracted` | ✅ | 4 candidates skipped (likely locations/items, not NPCs) |
| 13 | `universal.recent_events.ring_bounded` | ✅ | 2 entries |
| 13 | `universal.scene.npc_cap` | ✅ | 0 NPCs |
| 13 | `universal.pc.condition_no_dupes` | ✅ | 3 conditions, no dupes |
| 13 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 13 | `universal.momentum.band_delta` | ✅ | (no roll) |

## Turn Metrics

| # | input | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | retries | parse_fail | duration_s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | Walk over to Caron's table and sit down across f… | 1231 (+0) | 2489 (+0) | 3562 (-6) | 2160 (-6) | 2197 (-6) | 0 | 0 | 28.33 |
| 2 | I slide 500 credits across the table to Caron an… | 1311 (+4) | 2819 (-5) | 3934 | 2253 (+146) | 2299 (+151) | 0 | 0 | 26.41 |
| 3 | I find Halden by the town well and offer to carr… | 1312 (-1) | 3151 (+55) | 4041 (+55) | 2252 (-6) | 2553 (-1) | 0 | 0 | 32.21 |
| 4 | I leave Marrow's Crossing by the east gate and h… | 1316 (+5) | 3654 (+106) | 3972 (+77) | 2073 (+62) | 2252 (+86) | 0 | 0 | 27.24 |
| 5 | I walk up to the two toughs at the inn door and … | 1308 (+0) | 3954 (+106) | 3881 (+90) | 2368 (+161) | 2672 (+347) | 0 | 0 | 31.37 |
| 6 | I drop 200 credits on the ground between the tou… | 1313 (-4) | 4411 (+65) | 4043 (-54) | 2367 (-15) | 2545 (-37) | 0 | 0 | 38.04 |
| 7 | I sit across from Halden at his table, slide the… | 1312 (+3) | 3787 (+32) | 3897 (-219) | 2168 (-40) | 2450 (-23) | 0 | 0 | 26.71 |
| 8 | I pull out the brass key Halden gave me and try … | 1315 (-5) | 4071 (-109) | 3872 (-111) | 2283 (+185) | 2553 (+284) | 0 | 0 | 29.91 |
| 9 | I press my ear against the inn's stone wall and … | 1308 (-4) | 4327 (-100) | 3825 | — | 2138 (-77) | 0 | 0 | 25.63 |
| 10 | I approach Matthew Estrada at the bar, grab his … | 1317 (-11) | 4809 (+83) | 4024 (+293) | 2268 (+6) | 2286 (-124) | 0 | 0 | 30.48 |
| 11 | Matthew's bodyguard draws a knife! I tackle him … | 1309 (-8) | 5171 (+46) | 3947 (+42) | 2304 (-72) | 2535 (+16) | 0 | 0 | 31.04 |
| 12 | I grab the ledger from my coat and sprint out th… | 1304 (-2) | 5618 (-32) | 4008 (-24) | 2340 (+154) | 2315 (+139) | 0 | 0 | 40.01 |
| 13 | I find a quiet corner at the dock and wrap my wo… | 1316 (-5) | 3801 (+128) | 3946 (+82) | 2330 (+158) | 2620 (+256) | 0 | 0 | 31.52 |
|  | TOTALS | 16972 | 52062 | 50952 | 27166 | 31415 | 0 | 0 | 398.91 |

**Total turns:** 13 · **Total duration:** 398.91s · **Avg/turn:** 30.69s
**Total tokens in:** 178,567 · **Total tokens out:** 140,848 · **Total LLM time:** 383.5s
**Total retries:** 0 · **Total parse failures:** 0


## Warnings (≥ warn threshold but < fail threshold)

- `extraction.progress` turn 5: 2325 → 2672 (+14.9%)
- `extraction.progress` turn 8: 2269 → 2553 (+12.5%)
- `extraction.progress` turn 13: 2364 → 2620 (+10.8%)
