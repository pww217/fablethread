# Eval Report — `full_cycle`

**Pack:** `eval-pack` · **Model:** `mlx-community/gemma-4-26b-a4b-it-mxfp8` · **Temp override:** `None`  
**Started:** 2026-05-09T05:17:42.620279+00:00 · **Finished:** 2026-05-09T05:22:07.333679+00:00  
**Output dir:** `/Users/pwilson/Repos/ccya/evals/runs/20260509T051742Z_j4nui1sa`  
**Compared against:** _(no prior run found)_

## Judge Summary

**Mechanical:** 3/5  
**Narrative:** 4/5  
**Rubric:** `/Users/pwilson/Repos/ccya/evals/rubrics/default.md`
**Judge model:** `mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit`

**Pipeline scores:**
- rules: 4/5
- narrate: 3/5
- extract_scene: 4/5
- extract_state: 2/5
- extract_progress: 2/5

**Trace:** [`full_cycle.trace.md`](full_cycle.trace.md)
**Judge response:** [`full_cycle.judge.md`](full_cycle.judge.md)

## ✅ No flags

No regressions, retries, failures, or judge score drops detected.


## Auto-Checker

**100 passed, 19 failed**

| Turn | Assertion | Result | Detail |
|---|---|---|---|
| 2 | `rules.rolled` | ❌ | rolled=True |
| 2 | `universal.recent_events_add.turn_stamped` | ❌ | 1 entries had turn=0/null instead of 2: ['Caron refuses to negotiate and demands labor in lieu of coin.'] |
| 2 | `universal.pending_gm_beat.consumed` | ✅ | (first turn) |
| 2 | `universal.location_change.applied` | ✅ | (no change) |
| 2 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 2 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Voss'] |
| 2 | `universal.recent_events.ring_bounded` | ✅ | 4 entries |
| 2 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 2 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 2 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 2 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 3 | `rules.rolled` | ❌ | rolled=False |
| 3 | `extract.state.inventory_remove` | ✅ | inventory_remove[credits] amount=500 |
| 3 | `extract.progress.quest_updates` | ❌ | quest_updates[settle_the_debt] not found |
| 3 | `universal.recent_events_add.turn_stamped` | ❌ | 1 entries had turn=0/null instead of 3: ['Tyler, a menacing man in a leather jerkin, enters the inn and eyes your credits.'] |
| 3 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 3 | `universal.location_change.applied` | ✅ | (no change) |
| 3 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 3 | `universal.npc_mention.extracted` | ✅ | 7 candidates skipped (likely locations/items, not NPCs) |
| 3 | `universal.recent_events.ring_bounded` | ✅ | 5 entries |
| 3 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 3 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 3 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 3 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 4 | `rules.rolled` | ❌ | rolled=False |
| 4 | `extract.progress.quest_updates` | ✅ | quest_updates[deliver_the_ledger] found |
| 4 | `universal.recent_events_add.turn_stamped` | ❌ | 1 entries had turn=0/null instead of 4: ['Halden has hired Voss to deliver the ledger for 200 credits.'] |
| 4 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 4 | `universal.location_change.applied` | ✅ | marrows_crossing -> town_square |
| 4 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 4 | `universal.npc_mention.extracted` | ✅ | 9 candidates skipped (likely locations/items, not NPCs) |
| 4 | `universal.recent_events.ring_bounded` | ✅ | 6 entries |
| 4 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 4 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 4 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 4 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 5 | `rules.rolled` | ✅ | rolled=False |
| 5 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=5 |
| 5 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 5 | `universal.location_change.applied` | ✅ | (no change) |
| 5 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 5 | `universal.npc_mention.extracted` | ✅ | 6 candidates skipped (likely locations/items, not NPCs) |
| 5 | `universal.recent_events.ring_bounded` | ✅ | 7 entries |
| 5 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 5 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 5 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 5 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 6 | `rules.rolled` | ✅ | rolled=True |
| 6 | `extract.scene.scene_tags` | ❌ | scene_tags[combat] not found |
| 6 | `universal.recent_events_add.turn_stamped` | ❌ | 1 entries had turn=0/null instead of 6: ['Bald Tough and Scarred Tough are demanding a toll to enter the Crossed Keys Inn.'] |
| 6 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 6 | `universal.location_change.applied` | ✅ | town_square -> crossed_keys_inn_entrance |
| 6 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 6 | `universal.npc_mention.extracted` | ✅ | 5 candidates skipped (likely locations/items, not NPCs) |
| 6 | `universal.recent_events.ring_bounded` | ✅ | 8 entries |
| 6 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 6 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 6 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 6 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 7 | `rules.rolled` | ❌ | rolled=False |
| 7 | `extract.state.inventory_remove` | ✅ | inventory_remove[credits] amount=200 |
| 7 | `extract.progress.quest_updates` | ❌ | quest_updates[clear_the_road_toughs] not found |
| 7 | `universal.recent_events_add.turn_stamped` | ❌ | 1 entries had turn=0/null instead of 7: ['The attempted bribe of the thugs has increased the tension on the inn steps.'] |
| 7 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 7 | `universal.location_change.applied` | ✅ | (no change) |
| 7 | `universal.narrate.binding_present` | ✅ | (no roll) |
| 7 | `universal.npc_mention.extracted` | ✅ | 5 candidates skipped (likely locations/items, not NPCs) |
| 7 | `universal.recent_events.ring_bounded` | ✅ | 9 entries |
| 7 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 7 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 7 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 7 | `universal.momentum.band_delta` | ✅ | (no roll) |
| 8 | `extract.progress.quest_updates` | ✅ | quest_updates[deliver_the_ledger] found |
| 8 | `extract.progress.quest_status` | ❌ | quest[deliver_the_ledger].status='active' (expected 'completed') |
| 8 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=8 |
| 8 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 8 | `universal.location_change.applied` | ✅ | (no change) |
| 8 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 8 | `universal.npc_mention.extracted` | ✅ | 6 candidates skipped (likely locations/items, not NPCs) |
| 8 | `universal.recent_events.ring_bounded` | ✅ | 10 entries |
| 8 | `universal.scene.npc_cap` | ✅ | 3 NPCs |
| 8 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 8 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 8 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 9 | `rules.rolled` | ✅ | rolled=True |
| 9 | `extract.state.inventory_remove` | ❌ | inventory_remove[brass_key] not found |
| 9 | `universal.recent_events_add.turn_stamped` | ✅ | all 1 entries stamped with turn=9 |
| 9 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 9 | `universal.location_change.applied` | ✅ | crossed_keys_inn_entrance -> crossed_keys_inn_service_corridor |
| 9 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 9 | `universal.npc_mention.extracted` | ✅ | 5 candidates skipped (likely locations/items, not NPCs) |
| 9 | `universal.recent_events.ring_bounded` | ✅ | 11 entries |
| 9 | `universal.scene.npc_cap` | ✅ | 0 NPCs |
| 9 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 9 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 9 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 10 | `rules.rolled` | ✅ | rolled=True |
| 10 | `extract.scene.scene_tags` | ❌ | scene_tags[social] not found |
| 10 | `universal.recent_events_add.turn_stamped` | ❌ | 1 entries had turn=0/null instead of 10: ['Kathryn, a suspicious kitchen worker, confronts Voss in the service corridor.'] |
| 10 | `universal.pending_gm_beat.consumed` | ✅ | beat consumed or replaced |
| 10 | `universal.location_change.applied` | ✅ | (no change) |
| 10 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 10 | `universal.npc_mention.extracted` | ✅ | 5 candidates skipped (likely locations/items, not NPCs) |
| 10 | `universal.recent_events.ring_bounded` | ✅ | 12 entries |
| 10 | `universal.scene.npc_cap` | ✅ | 7 NPCs |
| 10 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 10 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 10 | `universal.momentum.band_delta` | ✅ | (no momentum field) |
| 11 | `rules.rolled` | ✅ | rolled=True |
| 11 | `universal.recent_events_add.turn_stamped` | ❌ | 1 entries had turn=0/null instead of 11: ['Matthew Estrada displays the disciplined, watchful behavior of a trained soldier.'] |
| 11 | `universal.pending_gm_beat.consumed` | ✅ | (no prior beat) |
| 11 | `universal.location_change.applied` | ✅ | crossed_keys_inn_service_corridor -> crossed_keys_inn_tavern |
| 11 | `universal.narrate.binding_present` | ✅ | binding directive included |
| 11 | `universal.npc_mention.extracted` | ❌ | narration mentions names not in npc_add/update or known: ['Who', 'Instead', 'Walk'] |
| 11 | `universal.recent_events.ring_bounded` | ✅ | 13 entries |
| 11 | `universal.scene.npc_cap` | ✅ | 2 NPCs |
| 11 | `universal.pc.condition_no_dupes` | ✅ | 2 conditions, no dupes |
| 11 | `universal.progress.actions_quality` | ✅ | 4 distinct actions |
| 11 | `universal.momentum.band_delta` | ✅ | (no momentum field) |

## Turn Metrics

| # | input | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | retries | parse_fail | duration_s |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | Walk over to Caron's table and sit down across f… | 1015 | 2313 | 3295 | — | 1453 | 0 | 0 | 23.24 |
| 3 | I slide 500 credits across the table to Caron an… | 1093 | 2723 | — | 1872 | 1607 | 0 | 0 | 18.36 |
| 4 | I find Halden by the town well and offer to carr… | 1095 | 2973 | 3703 | 1891 | 2098 | 0 | 0 | 32.67 |
| 5 | I leave Marrow's Crossing by the east gate and h… | 1090 | 3382 | — | 1852 | 1934 | 0 | 0 | 19.20 |
| 6 | I walk up to the two toughs at the inn door and … | 1086 | 3746 | 3589 | 2011 | 1856 | 0 | 0 | 32.18 |
| 7 | I drop 200 credits on the ground between the tou… | 1103 | 4243 | — | 1911 | 1824 | 0 | 0 | 20.89 |
| 8 | I sit across from Halden at his table, slide the… | 1087 | 4610 | — | 2012 | 2109 | 0 | 0 | 26.64 |
| 9 | I pull out the brass key Halden gave me and try … | 1090 | 4910 | 3695 | 1909 | 1779 | 0 | 0 | 33.94 |
| 10 | I press my ear against the inn's stone wall and … | 1097 | 5142 | — | 2027 | 1911 | 0 | 0 | 24.21 |
| 11 | I approach Matthew Estrada at the bar, grab his … | 1098 | 5459 | 3739 | 1964 | 1766 | 0 | 0 | 33.33 |
|  | TOTALS | 10854 | 39501 | 18021 | 17449 | 18337 | 0 | 0 | 264.65 |

**Total turns:** 10 · **Total duration:** 264.65s · **Avg/turn:** 26.46s
**Total tokens in:** 104,162 · **Total tokens out:** 74,631 · **Total LLM time:** 264.3s
**Total retries:** 0 · **Total parse failures:** 0


## Judge Verdict (full)

# Mechanical Design Critique

## Pipeline: rules
**Trace**
Turn 2: Input `Walk over to Caron's table...` → LLM outputs `IntentEnvelope` with `intent_verb: negotiate`, `check.required: true`, `skill: charisma`, `difficulty: normal` → Python rolls `3+2+1-0 = 6` → Band `fail` → Directive `The negotiate fails. The attempt fails outright...` → Narrate receives directive.

**What Went Well**
The anti-declare-outcome rule is effectively enforced. In Turn 2, the player phrases a negotiation attempt, and the rules pipeline correctly classifies it as a charisma check with a real consequence (Caron refuses), preventing the player from narrating success. The dice resolution math is accurate, and the `directive` field cleanly translates mechanical outcomes into narrative latitude for the next step.

**What Went Poorly**
`intent_verb` mapping is inconsistent. In Turn 8, the player delivers a ledger and seal to Halden, but the rules pipeline outputs `intent_verb: negotiate`. The verb list provided in the prompt (`attack|persuade|sneak|hack|deceive|intimidate|climb|repair|recall|escape|negotiate`) lacks a precise fit for "deliver/complete transaction," forcing the LLM to default to `negotiate`. This creates a semantic mismatch between the player's action and the engine's classification.

**Prompt Analysis**
The rules prompt is well-structured but lacks explicit enum constraints for `intent_verb`. The LLM frequently picks verbs that are close but not exact (e.g., `negotiate` for delivery, `hack` for lockpicking). The prompt could be tightened by providing a 1:1 mapping guide or allowing free-text verbs with a validation step.

**Mechanic Placement**
Intent classification and dice resolution correctly live in Step 0. The `directive` output properly gates narrator latitude. No misplaced mechanics detected.

**Issues**
- **`intent_verb` semantic drift** (Turns 2, 8) — Failure mode: `scope/domain mismatch`. The verb list doesn't cover common non-combat actions like `deliver` or `examine`, causing LLMs to force-fit `negotiate` or `hack`. Remediation: Expand the verb list to include `deliver`, `examine`, `search`, or explicitly allow free-text verbs with a note to pick the closest match.

**Pipeline Score (1-5)**
4

## Pipeline: narrate
**Trace**
Turn 2: Receives `RulesOutcome` (FAIL), `pack_style`, `pending_gm_beat` (null) → LLM generates prose describing Caron's refusal, honors the `fail` directive by having Caron demand labor instead of coin → Emits `<scope>{"active_domains":["scene"]}</scope>` at the end.

**What Went Well**
The narrator excellently honors dice outcomes. A `fail` on charisma correctly results in Caron rejecting the negotiation and escalating the debt, rather than ignoring the roll. The prose adheres closely to the `eval-pack` style guide: concrete sensory details ("amber liquid," "tally stick," "stale ale"), plain language, and appropriate word count. The scope tail is correctly formatted and stripped server-side.

**What Went Poorly**
There is a direct contradiction between the Narrate System Prompt (`Second person, present tense`) and the World Pack Style (`second-person past-tense register`). The narrator mostly follows past tense, but occasionally slips into present or mixes tenses (e.g., Turn 5: "You take the Ledger... You turn away... The town square is thinning out"). This creates a jarring stylistic inconsistency. Additionally, the narrator sometimes invents details not prompted (e.g., Tyler following in Turn 5), which, while narratively interesting, bypasses the `gm_beat` pipeline's intended control.

**Prompt Analysis**
The narrator prompt is heavily bloated with full state dumps (PC bio, location, inventory, quests, recent events, known characters). This wastes ~300-400 tokens per turn. The `pack_style` is pasted verbatim into the prompt, duplicating instructions already in the system prompt.

**Mechanic Placement**
Prose generation and scope decision correctly live in Step 1. The `gm_beat` consumption (clearing `pending_gm_beat`) works as designed.

**Issues**
- **Tense contradiction** (All turns) — Failure mode: `scope/domain mismatch`. System prompt says present, style pack says past. Narrator defaults to past but occasionally fractures. Remediation: Align the Narrate System Prompt to explicitly mandate past tense, or remove the style pack from the prompt and rely on a dedicated style guide file.
- **Unprompted NPC invention** (Turn 5) — Failure mode: `messy logic`. Narrator introduces Tyler following the player without a `gm_beat` or explicit prompt signal, bypassing the scene extractor's pressure lifecycle. Remediation: Instruct narrator to only introduce new NPCs or state changes that are explicitly signaled by `gm_beat` or `active_domains`.

**Pipeline Score (1-5)**
3

## Pipeline: extract_scene
**Trace**
Turn 2: Receives narration + `rules_outcome` (FAIL) → LLM outputs `scene_tags: ["dialogue"]`, `scene_pressure_add: [{id: caron_collection_demand, urgency: building}]`, `gm_beat: {type: complication, ...}` → Delta applied.

**What Went Well**
Scene pressure lifecycle is handled correctly. Pressure is added on Turn 2, correctly removed on Turn 4 when the player leaves the immediate threat zone, and properly downgraded/removed on Turn 9 after a success. The `gm_beat` generation follows the prompt's strict entity-naming rule (e.g., naming "Tyler" and "tally stick" in Turn 2), producing actionable backstage instructions.

**What Went Poorly**
`location_description` is emitted too liberally. In Turn 4, the narrator describes the town square cooling down, and the extractor emits a `location_description` field. The prompt says "Only emit this field if the narration describes a meaningful environmental or atmospheric change," but minor lighting/weather shifts are triggering it. This bloats the state with redundant location metadata.

**Prompt Analysis**
The scene prompt is comprehensive but could be trimmed. The `npc_match instruction` is excellent for compendium hygiene. The `de-escalation` rules are clear.

**Mechanic Placement**
Scene tags, pressure, and GM beats correctly live in Step 2a. Location changes correctly gate the stream. No misplaced mechanics.

**Issues**
- **Over-triggered `location_description`** (Turns 4, 9) — Failure mode: `wasted tokens`. Minor atmospheric shifts trigger full description re-emissions. Remediation: Tighten the rule to require a *functional* change (e.g., "door broken," "crowd disperses," "lighting shifts to emergency") rather than descriptive prose.

**Pipeline Score (1-5)**
4

## Pipeline: extract_state
**Trace**
Turn 3: Receives narration + `rules_outcome` (no roll) → LLM outputs `inventory_remove: [{id: credits, amount: 500}]` → Delta applied. Credits correctly deducted.

**What Went Well**
The deduplication rule and ID matching instructions are strong. The extractor correctly refuses to add items not explicitly received and handles stack removals accurately. The `roll_context` guidance for conditions is well-placed, preventing spurious condition additions on clean successes.

**What Went Poorly**
Turn 5 exhibits a critical duplication failure. The narration says: *"You take the Ledger from Halden and tuck it securely into your pack, the weight of the task settling alongside the new Credits in your pouch."* The extractor outputs `inventory_add: [{id: credits, amount: 200}]`. This is a duplicate of the credits already in inventory from Turn 4. The extractor failed to cross-reference existing inventory or recent events, treating "new Credits" as a fresh acquisition rather than a narrative reference to existing funds.

**Prompt Analysis**
The state prompt is dense. The `Match instruction` says "check the existing inventory list provided in context," but the LLM ignores this when phrasing like "new Credits" appears. It needs a stronger directive to treat possessive references as state-locked unless explicitly transferred.

**Mechanic Placement**
Inventory and condition extraction correctly live in Step 2b. Skippable when domains are inactive. Correct.

**Issues**
- **Inventory duplication on possessive phrasing** (Turn 5) — Failure mode: `failed to input key information`. Extractor ignores existing inventory state when narration references items already owned. Remediation: Pass `items_gained` from Step 2c (or existing inventory) explicitly to Step 2b, or add a hard rule: "If an item is already in inventory, NEVER emit `inventory_add` for it. Use `inventory_update` or ignore."

**Pipeline Score (1-5)**
2

## Pipeline: extract_progress
**Trace**
Turn 2: Receives narration + `rules_outcome` (FAIL) → LLM outputs `recent_events_add: [{id: caron_debt_demand, text: "...", turn: 0}]`, `actions: [...]` → Delta applied.

**What Went Well**
Quest objective completion logic is robust. In Turn 8, the extractor correctly marks objectives 2 and 3 of `deliver_the_ledger` as done, allowing the quest to auto-complete. The `actions` generation provides distinct, plot-forward choices that respect the current scene state.

**What Went Poorly**
Two major schema drift issues:
1. `recent_events_add.turn` is consistently `0` across all turns (auto-checker failure). The prompt schema literally shows `"turn": 0` as an example, and the LLM copies it verbatim.
2. Quest ID duplication. In Turn 8, the extractor creates a *new* quest `deliver_ledger` with empty title/objectives, while simultaneously updating the correct `deliver_the_ledger`. This creates state bloat and ghost quests.
3. Action key inconsistency. Turn 8 outputs `{'text': '...'}` instead of `{'description': '...'}`, violating the schema.

**Prompt Analysis**
The progress prompt is bloated with full recent events and prior narration. The schema example for `recent_events_add` hardcodes `"turn": 0`, which is the root cause of the auto-checker failure. The prompt lacks explicit ID normalization rules for quests.

**Mechanic Placement**
Quest updates, recent events, and actions correctly live in Step 2c. Always runs. Correct.

**Issues**
- **`turn` field hardcoded to 0** (Turns 2, 3, 4, 6, 7, 10, 11) — Failure mode: `bad prompt`. Schema example shows `"turn": 0`, LLM copies it. Remediation: Change schema example to `{"turn": <current_turn>}` and add explicit instruction: "Replace 0 with the actual turn number."
- **Quest ID duplication** (Turn 8) — Failure mode: `schema drift`. Extractor creates `deliver_ledger` instead of matching `deliver_the_ledger`. Remediation: Add a strict ID normalization rule: "Always match existing quest IDs exactly. Do not create new quests with similar titles. If updating, use the existing `id`."
- **Action key inconsistency** (Turn 8) — Failure mode: `schema drift`. Outputs `text` instead of `description`. Remediation: Enforce exact key matching in schema examples.

**Pipeline Score (1-5)**
2

# Storytelling Design Critique

## quest_arc_quality
**Score:** 3
Quests advance logically but suffer from mechanical ID duplication (Turn 8 creates a ghost `deliver_ledger` quest). The "Settle the Old Debt" quest stalls because the player pays Caron but the extractor fails to mark objectives done (Turn 3), leaving it active indefinitely. This breaks the arc's closure.

## rewards_and_consequences
**Score:** 4
Failures carry real weight: credits are lost (Turns 3, 7, 10), tension escalates (Turn 6), and negotiation attempts fail outright (Turn 2). Successes grant tangible progress (credits, ledger delivery, backdoor access). Trade-offs feel meaningful.

## narrative_compellingness
**Score:** 4
The noir/merchant-road tone is consistent and engaging. Choices matter: sneaking through the service corridor (Turn 9) opens a new path, confronting Matthew (Turn 11) reveals character depth. The pacing keeps the player moving between social, exploration, and tension beats.

## genre_and_universe_fit
**Score:** 4
The plain, concrete style guide is respected. Sensory details ("floor wax," "stale grease," "tally stick") ground the fiction. The world feels lived-in, with factions (Caron, toughs, Halden) interacting organically.

## npc_development
**Score:** 3
Key NPCs like Caron and Matthew Estrada evolve meaningfully (Caron's predatory grin, Matthew's soldier-like vigilance). However, secondary NPCs (toughs, Kathryn) often feel like static obstacles or props rather than evolving characters. Their reactions are functional but lack deeper arcs.

## player_agency
**Score:** 4
Player choices consistently open new avenues. Failing to negotiate with Caron leads to paying credits. Failing to bribe toughs leads to sneaking in the back. Failures create options rather than dead-ends, preserving agency.

## pacing_and_pressure
**Score:** 4
Pressure mechanics escalate well: Caron's debt → road toll → Tyler's stalking → Kathryn's confrontation. The `scene_pressure` lifecycle correctly tracks urgency. Narrative pacing balances tension with breathing room (Turn 9's quiet corridor), though the narrator occasionally injects unsolicited complications (Turn 5).

# Prompt Redundancy Analysis

The harness detected 6 overlaps between `narrate` + `progress` and 2 between `narrate` + `scene`. 
1. **Narration fed to all 3 extractors**: Intentional per design. The extractors need the prose to parse state changes.
2. **PC Bio/Location/Inventory repeated across all 5 prompts**: Unintentional waste. Each turn, ~150-200 tokens of PC bio, location description, and inventory lists are duplicated across Rules, Narrate, Scene, State, and Progress prompts. Over 10 turns, this wastes ~3,000-4,000 tokens.
3. **Recent Events/Chronicle tail**: Repeated in Narrate and Progress prompts. Narrate needs history for tone; Progress needs it for event deduplication. Duplication is partially justified but could be surface-optimized.

**Top 3 dedup opportunities:**
- **PC Context Surface**: Pass a compacted `pc_context` block (name, stats, conditions, momentum) to all prompts instead of full bio/state. Saves ~50t/turn.
- **Inventory Snapshot**: Pass only `inventory_add`/`inventory_remove` deltas from previous turns to extractors, not full inventory lists. Saves ~80t/turn.
- **Chronicle Tail**: Limit `chronicle_tail` to 2 turns max for extractors. Narrate can keep 6. Saves ~100t/turn.

# Compaction Capabilities Report

Compaction did not fire during this run (run length: 10 turns).
- `[NA]` Bullet generation: Compaction did not fire.
- `[NA]` History pruning: Compaction did not fire.
- `[NA]` State sanitization: Compaction did not fire.
*Note: Compaction features cannot be evaluated on short runs. Recommend testing on 15+ turn traces.*

# Auto-Checker Failures

1. **`universal.recent_events_add.turn_stamped` (Turns 2, 3, 4, 6, 7, 10, 11)**
   - **WHY**: The Progress Extract prompt schema literally shows `"turn": 0` as a placeholder example. LLMs are highly prone to copy-pasting schema defaults. The extractor receives `turn: 0` instead of the actual turn number.
   - **Remediation**: Change the schema example to `{"turn": <current_turn>}` and add explicit instruction: "Replace 0 with the actual turn number from the prompt."

2. **`universal.npc_mention.extracted` (Turns 2, 11)**
   - **WHY**: False positives from the auto-checker regex. It flags common words like "Voss" (PC name, not NPC), "Who", "Instead", "Walk" (capitalized mid-sentence or dialogue) as untracked NPCs.
   - **Remediation**: Update the auto-checker regex to ignore PC names, dialogue quotes, and common capitalized words. Not a prompt/engine issue.

# Additional Observations

- **Tense Contradiction**: The Narrate System Prompt mandates "Second person, present tense," but the World Pack Style mandates "second-person past-tense register." The narrator defaults to past tense but occasionally fractures. This should be resolved at the prompt level.
- **Quest ID Normalization**: The engine lacks a strict ID normalization step between extraction and validation. `deliver_the_ledger` vs `deliver_ledger` creates duplicate quest objects in state. A pre-validation dedup step is needed.
- **GM Beat Consumption**: The `pending_gm_beat` is correctly cleared after use, but the narrator sometimes ignores it or invents its own complications (Turn 5), bypassing the scene pipeline's pressure lifecycle.

# Verdict

The engine's core 5-pipeline architecture is sound and produces compelling, mechanically consistent fiction. However, state extraction pipelines (State and Progress) suffer from schema drift and ID normalization failures that corrupt game state (duplicate credits, ghost quests, un-stamped events). These mechanical flaws cap the mechanical score at 3/5, while the narrative quality remains strong at 4/5. The single most important fix is to **standardize the Progress Extract schema examples (fixing the `turn: 0` copy-paste bug) and enforce strict ID normalization for quests and items during the delta merge phase** to prevent state bloat.

# Narrative Recap

Aren Voss arrives in Marrow's Crossing to settle a 500-credit debt with Caron, who refuses negotiation and demands labor. Aren pays the debt anyway, only to be confronted by road toughs demanding a toll at the Crossed Keys Inn. He sneaks through a service corridor, bribes a wall, and meets Kathryn, a sharp kitchen worker. He then confronts Matthew Estrada, a suspicious traveler with military precision, revealing a web of intrigue involving Halden's ledger, Tyler's stalking, and multiple factions vying for control of the inn and road.
