

---
mechanical_score: 3
narrative_score: 4
pipeline_scores:
  rules: 4
  narrate: 3
  extract_scene: 4
  extract_state: 3
  extract_progress: 2
---

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


# Mechanical Design Critique

## Pipeline: rules
### What Went Well
The rules pipeline consistently and correctly classifies player intent, selecting appropriate skills and difficulties. In Turn 5, it correctly identifies a persuasion attempt against resistant NPCs and triggers a charisma check. In Turn 11, it correctly routes a tackle/search action to a strength check. The anti-declare-outcome rule is respected; even when the player's input implies a specific result (e.g., T7 delivering a seal, T8 using a key), the engine rolls and applies the band, preventing player fiat.

### What Went Poorly
The rules pipeline occasionally struggles with compound or ambiguous inputs, defaulting to a single skill without clearly separating sub-actions in the `stakes` field. For example, in Turn 9, the player's input ("whisper to wall... offer credit to wall") is nonsensical, yet the rules engine rolls a charisma check and applies a fail band. While mechanically valid, the `stakes` field outputs a generic `[Mechanical cost: difficulty increase] + [Narrative consequence...]` template rather than a fiction-grounded cost, which weakens the forward dependency to the narrator.

### Prompt Analysis
The rules prompt is well-structured but slightly bloated with directive notes that rarely surface in the output. The `stakes` template instruction is redundant given the auto-generated narrative consequences. The prompt could be tightened by removing the explicit template and instead instructing the LLM to generate a single, concrete stake sentence that directly informs the narrator's complication directive.

### Mechanic Placement
Intent classification and dice resolution correctly live in Step 0. The `RulesOutcome` correctly shapes narrator latitude. No misplaced mechanics detected.

### Issues
- **Generic stakes generation** (Turns 5, 9, 10, 11) — Failure mode: `bad prompt`. Remediation: Replace the `stakes` template instruction with a directive to generate a single, concrete, fiction-grounded stake sentence that directly informs the narrator's complication or resolution.
- **Ambiguous input handling** (Turn 9) — Failure mode: `scope/domain mismatch`. Remediation: Add a fallback rule in the prompt: if the input is physically impossible or nonsensical, set `check.required=false` and emit a `narrate` directive for "pragmatic interpretation" rather than rolling a skill check.

### Pipeline Score (1-5)
4

## Pipeline: narrate
### What Went Well
The narrator consistently follows the second-person past-tense register and spatial clarity guidelines. It correctly binds dice bands to prose: Turn 5's `fail` produces a tense standoff without progressing the player's goal; Turn 6's `partial` introduces suspicion and a cost (the thugs keep the coin and block the path); Turn 12's `crit_success` delivers a clean escape with a concrete consequence (reaching the docks safely). The narrator also correctly consumes GM beats and pressure directives when present.

### What Went Poorly
The narrator repeatedly violates its own inventory verification constraint. In Turn 7, it describes sliding a `merchant_seal` across the table, but `merchant_seal` is not in the inventory list. In Turn 9, it describes pressing a `single iron coin` against the wall, but the inventory only contains `credits`. In Turn 13, it describes pressing `a few coins` into a boy's palm, triggering a rejected delta. This breaks mechanical trust and causes downstream extraction failures. Additionally, the narrator's bolding of items and locations triggers false-positive auto-checker failures.

### Prompt Analysis
The inventory verification instruction is present but ineffective against the model's generative tendencies. The prompt mixes strict constraints ("verify the item appears in the inventory list") with creative directives ("use colorful imagery, metaphors/similes"), causing the model to prioritize prose over state accuracy. The bolding instruction for items/NPCs also conflicts with the auto-checker's naive capitalization regex.

### Mechanic Placement
Narration correctly lives in Step 1. The `<scope>` tail correctly gates extractors. No misplaced mechanics.

### Issues
- **Inventory hallucination** (Turns 7, 9, 13) — Failure mode: `failed to input key information | bad prompt`. Remediation: Add a strict pre-narration validation step in the engine that strips or replaces any item names not in the provided inventory list before sending to the LLM, or add a stronger system prompt directive: "If an item is not in the inventory list, DO NOT mention it by name. Use a generic descriptor."
- **Bold formatting conflicts** (Turns 2-10) — Failure mode: `wasted tokens | schema drift`. Remediation: Instruct the narrator to use backticks or italics for items instead of bold, or update the auto-checker regex to ignore bolded non-NPC tokens.

### Pipeline Score (1-5)
3

## Pipeline: extract_scene
### What Went Well
The scene extractor reliably tracks NPC presence, location changes, and scene pressure lifecycle. It correctly removes NPCs when the player leaves a location (Turn 4 removes Caron, Turn 8 removes toughs). It correctly adds and updates pressures (`ledger_delivery_deadline`, `inn_entrance_confrontation`, `tavern_chaos`) and downgrades/removes them on success (Turn 7, Turn 8, Turn 12). The compendium NPC matching logic works well, avoiding duplicate entries for known characters.

### What Went Poorly
The extractor occasionally emits redundant or overly verbose `npc_update` notes that repeat information already in the compendium. In Turn 13, it updates `kenneth_miller`, `caron`, and `matthew_estrada` with notes that are better suited for `recent_events` or compendium history, cluttering the scene state. It also sometimes misses `npc_remove` when the player physically leaves a location but the narration doesn't explicitly state the NPC departed (e.g., Turn 7 removes toughs, but Turn 8 removes them again redundantly).

### Prompt Analysis
The scene prompt is comprehensive but slightly over-constrained on NPC update rules, causing the LLM to update notes even when only minor narrative shifts occur. The prompt could benefit from a stricter threshold: only emit `npc_update` when the NPC's situation, position, or relationship state meaningfully changes, not just when they are mentioned.

### Mechanic Placement
Scene extraction correctly lives in Step 2a. GM beat generation is correctly placed here. No misplaced mechanics.

### Issues
- **Over-eager NPC updates** (Turn 13) — Failure mode: `messy logic | wasted tokens`. Remediation: Add a threshold rule: "Only emit `npc_update` if the NPC's active situation, position, or relationship to the player has changed meaningfully. Do not update notes for mere mentions or last-seen tracking."
- **Redundant NPC removal** (Turn 8) — Failure mode: `scope/domain mismatch`. Remediation: Instruct the extractor to check `recently_left` or compendium last-seen data before emitting `npc_remove` to avoid duplicate removals.

### Pipeline Score (1-5)
4

## Pipeline: extract_state
### What Went Well
The state extractor correctly handles inventory deltas when items are explicitly named and present in the inventory list (Turn 2 removes 500 credits). It correctly applies condition lifecycles, adding `blackmailed`, `shaken`, and `concussed` in response to narrative events and roll outcomes. The condition guidance tied to roll context works well, ensuring conditions are only added when narratively and mechanically justified.

### What Went Poorly
The state extractor inherits the narrator's inventory hallucination problem. In Turn 7, it attempts to remove `merchant_seal`, which is rejected by the validator. In Turn 9, it attempts to remove `iron_coin`, also rejected. In Turn 13, it attempts to remove `credits` (which were already removed in Turn 2), causing a rejection. Additionally, it sometimes adds duplicate conditions (e.g., `concussed` added in Turn 11 and again in Turn 12, `shaken` added in Turn 9 and again in Turn 10) because it lacks a strict deduplication check against the current `pc.conditions` list before emitting `pc_condition_add`.

### Prompt Analysis
The state prompt instructs the LLM to "Always check against existing inventory before adding or removing an item," but this instruction is consistently ignored by the model. The prompt needs a stronger, explicit validation step: "If the item ID does not exist in the provided inventory list, DO NOT emit `inventory_remove` or `inventory_add`. Emit empty array instead." The condition deduplication rule is present but needs to be enforced by the engine's pre-prompt state injection or by a stricter LLM directive.

### Mechanic Placement
State extraction correctly lives in Step 2b. Cross-stream data (`items_gained`, `items_lost`) correctly feeds Step 2c. No misplaced mechanics.

### Issues
- **Inventory verification failure** (Turns 7, 9, 13) — Failure mode: `failed to input key information | bad prompt`. Remediation: Add a pre-prompt inventory validation step in the engine that replaces any hallucinated item names with `null` or strips them before sending to the LLM. Alternatively, add a strict system prompt rule: "If an item is not in the inventory list, output `[]` for inventory_add/remove."
- **Duplicate condition extraction** (Turns 9, 10, 11, 12) — Failure mode: `messy logic`. Remediation: Instruct the LLM to check the `active_conditions` list and only emit `pc_condition_add` if the ID is not already present. The engine should also enforce a deduplication filter in the delta merge step.

### Pipeline Score (1-5)
3

## Pipeline: extract_progress
### What Went Well
The progress extractor correctly handles quest objective completion when explicitly narrated (Turn 1 completes obj 1, Turn 2 completes obj 2 and marks quest completed, Turn 7 completes objs 2 & 3). It correctly generates `recent_events` that track meaningful plot points and updates `actions` suggestions that align with current quest states. The contact/meet objective rule works correctly, allowing narrative presence to complete objectives without dice rolls.

### What Went Poorly
**Critical Bug:** In Turns 5 and 6, the progress extractor emits `quest_updates` with an empty `objectives: []` array for `deliver_the_ledger` and `clear_the_road_toughs` respectively. This clears all existing objectives, causing a schema drift and losing quest progress. The extractor should preserve existing objectives when not updating them, or only emit updates for changed indices. Additionally, GM beats are consistently `null` despite frequent momentum shifts and quest stalls, indicating the trigger conditions in the prompt are not being followed by the LLM.

### Prompt Analysis
The progress prompt's quest update instruction is ambiguous regarding unchanged objectives. It says "Update existing: ... objectives: [...]" but doesn't explicitly instruct the LLM to preserve the full objectives array if only one index changes. The GM beat trigger conditions are buried in a long list and lack a fallback directive, causing the LLM to default to `null`.

### Mechanic Placement
Progress extraction correctly lives in Step 2c. Quest objective completion correctly gates on roll bands and narrative presence. GM beat generation is incorrectly placed here per the architecture (it belongs in Step 2a/Scene Extract), but since it's emitted here, it's a placement mismatch. The prompt says GM beats are sourced from scene stream, not progress. This is a `misplaced mechanic`.

### Issues
- **Quest objectives cleared to `[]`** (Turns 5, 6) — Failure mode: `messy logic | schema drift`. Remediation: Add explicit instruction: "When updating a quest, ALWAYS include the full existing objectives array. Only change the `done` or `failed` status for indices that actually changed. Never emit an empty objectives array."
- **GM beats consistently null** (Turns 1-13) — Failure mode: `bad prompt | misplaced mechanic`. Remediation: Move GM beat generation to Step 2a (Scene Extract) as documented in the architecture. Simplify trigger conditions in the prompt and add a fallback: "If momentum >= +2 or <= -2, or a quest is stalled for 3+ turns, emit a GM beat. Do not default to null."
- **Recent events deduplication** (Turns 3, 5, 6) — Failure mode: `wasted tokens`. Remediation: Instruct the LLM to check `recent_events` and `world_state` before emitting `recent_events_add`. The engine should also run a deduplication filter before applying deltas.

### Pipeline Score (1-5)
2


# Storytelling Design Critique

### quest_arc_quality
Score: 3
The quests form a logical progression, but stalled quests (`deliver_the_ledger`, `clear_the_road_toughs`) feel ignored by the engine after their initial setup. The progress extractor's objective-clearing bug in Turns 5-6 severely damages arc continuity, making it seem like quest data was lost. The debt quest completes satisfyingly, but the other two lack meaningful resolution or escalation by Turn 13.

### rewards_and_consequences
Score: 4
Dice bands are consistently honored. Failures produce complications (Turn 5 standoff, Turn 9 wall rejection), partials produce costs (Turn 6 suspicion/leverage, Turn 11 tackle/crash), and successes/crits produce clean resolutions (Turn 7 delivery, Turn 12 escape). Momentum moves correctly per band. Conditions are applied for costs, though sometimes duplicated. The consequence system works structurally and narratively.

### narrative_compellingness
Score: 4
The story maintains tension through escalating pressures and NPC interactions. The transition from debt settlement to courier delivery to tavern confrontation creates a natural dramatic arc. Choices matter, and failures open new paths (side door, escape to docks). The prose is engaging and adheres to the plain, clear style guide.

### npc_development
Score: 3
NPCs react meaningfully to player actions (Caron's patience, Halden's urgency, toughs' aggression, Matthew's calm threat). However, NPC presence tracking is sometimes inconsistent, and some NPCs are removed/added redundantly. The compendium updates work well, but scene-level NPC notes sometimes clutter state without advancing development.

### world_consistency
Score: 2
The narrator repeatedly invents items (`merchant_seal`, `iron_coin`) not present in the inventory, breaking mechanical trust and causing validator rejections. While the prose is consistent, the inventory hallucination is a significant consistency failure that undermines the engine's reliability.

### player_agency
Score: 4
The engine respects player input, even when it's absurd (T9 offering credit to a wall). Failures create new options rather than dead-ends (toughs block -> side door -> escape). The narrator correctly interprets intent pragmatically and lets dice decide outcomes.

### consequence_persistence
Score: 4
Conditions (`bruised ribs`, `low morale`, `blackmailed`, `shaken`, `concussed`) persist across turns and accumulate correctly. Scene pressures escalate and resolve appropriately. The only issue is occasional duplicate condition extraction, but the engine's state snapshot shows they are managed correctly.

### pacing_and_pressure
Score: 4
Pressures (`ledger_delivery_deadline`, `inn_entrance_confrontation`, `tavern_chaos`) escalate correctly and are removed on success. The narration reflects urgency levels, and breathing room is provided after successes. The pacing feels tight and purposeful.

### momentum_arc
Score: 3
Momentum oscillates: 0 → -1 → 0 → 1 → 0 → -1 → 1 → 1. It correlates somewhat with roll outcomes but lacks a clear rising/falling arc. The engine's momentum deltas are applied correctly, but the session's shape is more reactive than dramatic. A clearer peak and resolution would strengthen the arc.


# Prompt Redundancy Analysis

The auto-detected overlaps are largely intentional by design: the full narration and recent events are fed to all three extractors to ensure they have sufficient context. However, this creates significant token waste.

1. **Narrate + Progress overlap (Recent Events block):** The `## Recent Events` block is duplicated verbatim in both the narrate and progress prompts. This is intentional but wastes ~150-200 tokens per turn.
2. **Narrate + Scene overlap (Location description):** The location description is duplicated. Intentional, but redundant.
3. **Cross-stream NPC/Inventory duplication:** The full NPC and inventory lists are repeated across narrate, scene, and state prompts. This is by design for verification but could be condensed.

**Top 3 dedup opportunities:**
- **Condense Recent Events feed:** Instead of passing the full `recent_events` array to all extractors, pass a compressed summary surface (e.g., 3-4 key bullet points) to extractors, keeping the full array only in the narrate prompt.
- **Remove redundant Location blocks:** The scene extractor already receives `state.location`. The narrate prompt can omit the full location description and instead pass a `location_summary` string.
- **Cross-stream NPC/Inventory summaries:** Replace full NPC/inventory lists in extractors with a `state_surface` object containing only IDs, names, and amounts. This reduces prompt size by ~30% without losing extraction accuracy.


# Compaction Capabilities Report

**Compaction at turn 6:**
- `bullet_named_npcs`: [OK] Bullets correctly reference Caron, Halden, and Edda.
- `bullet_location`: [OK] Locations (tavern, inn) are preserved.
- `bullet_quest_outcomes`: [OK] Debt cleared, contract accepted.
- `bullet_key_items`: [NA] No major item gains/losses in T1-3.
- `bullet_conditions`: [NA] No conditions added in T1-3.
- `bullet_irreversible`: [OK] Debt payment is irreversible and noted.
- `bullet_deaths`: [NA] No deaths.
- `bullet_mech_consequences`: [OK] Contract acceptance noted.
- `bullet_culling`: [OK] Atmospheric details removed, key actions preserved.
- `sanitize_npc_merge`: [NA] No duplicates.
- `sanitize_inventory`: [NA] No duplicates.
- `sanitize_quest_close`: [FAIL] `settle_the_debt` completed at T2, but compaction does not close it or remove it from active state.
- `sanitize_pressure`: [NA] No pressures added in T1-3.
- `sanitize_condition`: [NA] No conditions added in T1-3.

**Compaction at turn 12:**
- `bullet_named_npcs`: [OK] Toughs, Halden, Kenneth Miller referenced.
- `bullet_location`: [OK] Marrow's Crossing, inn, docks noted.
- `bullet_quest_outcomes`: [OK] Ledger delivered, toughs confronted.
- `bullet_key_items`: [OK] Ledger, brass key, bundle noted.
- `bullet_conditions`: [OK] Injuries and concussion noted.
- `bullet_irreversible`: [OK] Escape from inn is irreversible.
- `bullet_deaths`: [NA] No deaths.
- `bullet_mech_consequences`: [OK] Thugs' suspicion, bundle acquisition noted.
- `bullet_culling`: [OK] Combat and travel details culled, key beats preserved.
- `sanitize_npc_merge`: [NA] No duplicates.
- `sanitize_inventory`: [NA] No duplicates.
- `sanitize_quest_close`: [FAIL] `settle_the_debt` remains open in state; compaction does not close it.
- `sanitize_pressure`: [FAIL] `tavern_chaos` pressure resolved at T12, but compaction does not remove it from state.
- `sanitize_condition`: [FAIL] `concussed` and `shaken` conditions persist but are not marked for removal or resolution by compaction.

**Overall Compaction Score:** The bullet generation is strong and faithful. However, the sanitization phase is completely inactive. The compactor fires but records `(none recorded)` for all sanitization actions. This is a critical mechanical failure. The compactor must run `quest_close`, `pressure_remove`, and `condition_remove` logic and apply it to the state.


# Auto-Checker Failures

The auto-checker failures for `universal.npc_mention.extracted` across Turns 2-10 are **false positives**. The checker's regex appears to flag any capitalized word or bolded token in the narration as a potential NPC mention, ignoring context. Examples flagged: `['Credits', 'Slowly', 'Crossed', 'Marrow', 'Crossing', 'Instead', 'Matthew', 'Estrada']`. `Credits`, `Crossed`, `Marrow`, `Crossing`, and `Instead` are clearly not NPC names. The narrator's bolding of items and locations (`**Credits**`, `**Crossed Keys Inn**`) triggers the naive checker.

**Remediation:** Update the auto-checker regex to ignore tokens that are:
1. Bolded and match known inventory IDs or location names.
2. Common adverbs/prepositions (`Instead`, `Slowly`).
3. Pluralized currency terms (`Credits`).
Alternatively, instruct the narrator to use backticks or italics for items/locations instead of bold to avoid triggering capitalization-based NPC detectors.


# Additional Observations

- **GM Beat Null Consistency:** The GM beat is `null` in every single turn despite frequent momentum shifts and quest stalls. The prompt's trigger conditions are likely too complex or buried, causing the LLM to default to safe `null`. This mechanic is structurally present but functionally dead.
- **Validator Rejections:** The engine correctly rejects invalid inventory removals (`merchant_seal`, `iron_coin`, `credits`), but the narrator's hallucination wastes tokens and confuses downstream extractors. A pre-narration inventory validation step would save significant compute and improve state accuracy.
- **Momentum Oscillation:** Momentum fluctuates without a clear narrative arc. The engine applies deltas correctly, but the session lacks a deliberate pacing strategy to build momentum toward a peak.


# Verdict

The engine demonstrates strong mechanical foundations in dice resolution, pressure lifecycle, and narrative binding, but is hampered by three critical flaws: the narrator's inventory hallucination, a progress extractor bug that clears quest objectives, and a completely inactive compaction sanitization phase. The auto-checker false positives are a configuration issue, not a design flaw. The narrative is compelling and respects player agency, but mechanical trust is eroded by state inconsistencies. Fix the progress extractor's objective preservation, activate the compactor's sanitization pipeline, and enforce inventory verification before narration to elevate this engine to a 4/5 or 5/5.


# Actionable Issues and Remediations

### Major
- **[Engine/Prompt] Quest objectives cleared to `[]`** (Turns 5, 6) — The progress extractor emits empty objective arrays, losing quest progress. Remediation: Add explicit instruction: "When updating a quest, ALWAYS include the full existing objectives array. Only change the `done` or `failed` status for indices that actually changed. Never emit an empty objectives array."
- **[Engine/Compactor] Sanitization phase inactive** (Turns 6, 12) — The compactor fires but records zero sanitization actions, leaving completed quests, resolved pressures, and expired conditions in state. Remediation: Ensure the compactor pipeline runs `quest_close`, `pressure_remove`, and `condition_remove` logic after bullet generation and applies these deltas to the state before persisting.
- **[Engine/Prompt] GM beats consistently null** (Turns 1-13) — The mechanic is dead despite frequent triggers. Remediation: Move GM beat generation to Step 2a (Scene Extract) as documented. Simplify trigger conditions and add a fallback: "If momentum >= +2 or <= -2, or a quest is stalled for 3+ turns, emit a GM beat. Do not default to null."

### Minor
- **[Prompt] Inventory hallucination by narrator** (Turns 7, 9, 13) — Narrator invents items not in inventory, causing validator rejections and extraction failures. Remediation: Add a strict pre-prompt directive: "If an item is not in the inventory list, DO NOT mention it by name. Use a generic descriptor." The engine should also run a pre-narration validation step to strip hallucinated item names.
- **[Auto-Checker] False positive NPC mentions** (Turns 2-10) — Naive regex flags bolded items/locations and common words as NPC mentions. Remediation: Update checker regex to ignore bolded inventory/location tokens and common adverbs/prepositions, or change narrator formatting to backticks/italics for items.
- **[Prompt] Over-eager NPC updates** (Turn 13) — Scene extractor updates notes for mere mentions, cluttering state. Remediation: Add threshold rule: "Only emit `npc_update` if the NPC's active situation, position, or relationship to the player has changed meaningfully."

### Trivial
- **[Prompt] Generic stakes template** (Turns 5, 9, 10, 11) — Rules pipeline emits boilerplate stakes. Remediation: Replace template instruction with a directive to generate a single, concrete, fiction-grounded stake sentence.
- **[Prompt] Redundant location blocks** — Location description duplicated across narrate and scene prompts. Remediation: Pass a `location_summary` string to extractors instead of full description blocks to save tokens.