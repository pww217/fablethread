

---
mechanical_score: 3
narrative_score: 4
pipeline_scores:
  rules: 4
  narrate: 5
  extract_scene: 3
  extract_state: 3
  extract_progress: 3
---

# Table of Contents
- [Mechanical Design Critique](#mechanical-design-critique)
- [Storytelling Design Critique](#storytelling-design-critique)
- [Prompt Redundancy Analysis](#prompt-redundancy-analysis)
- [Compaction Capabilities Report](#compaction-capabilities-report)
- [Auto-Checker Failures](#auto-checker-failures)
- [Additional Observations](#additional-observations)
- [Verdict](#verdict)
- [Actionable Issues and Remediations](#actionable-issues-and-remediations)

# Mechanical Design Critique

## Pipeline: rules
### Trace
**Turn 3:** User input offers to carry ledger for 200 credits. Rules system outputs `intent_verb: negotiate`, `skill: charisma`, `difficulty: easy`, `check.required: true`. Python resolves 2d6+3+1-1=9 → `partial`. Directive: "partial success, they hold leverage."
**Turn 7:** User input attempts to use seal/ledger to Halden. Rules system outputs `intent_verb: persuade`, `target: Halden`, `skill: charisma`, `difficulty: normal`. Halden is not in `present_npcs`; the toughs are. Python resolves 2d6+3+0-0=8 → `partial`.

### What Went Well
- Intent classification is highly accurate. The system correctly distinguishes between routine commerce (T1, T2) and social negotiation (T3, T5, T6, T10).
- Dice resolution and band mapping are flawless. The `partial` band consistently produces the intended "success with complication" directive, which the narrator faithfully executes.
- Anti-declare-outcome and compound action rules are respected. The system correctly forces checks for social leverage attempts.

### What Went Poorly
- **Target grounding:** In T7, the rules extractor targets `Halden` despite Halden not being in the scene. The `present_npcs` list is passed to the rules prompt, but the LLM hallucinates the target based on the player's intent rather than scene reality. This breaks the forward dependency chain.
- **Intent verb mapping:** T9 maps "offer a single credit to the wall" to `intent_verb: persuade`. The prompt allows flexibility, but the system should flag or default to `deceive`/`sneak` or explicitly reject absurd targets, rather than rolling charisma against inanimate objects.

### Prompt Analysis
- The rules prompt lacks a strict "target must be from `present_npcs` or `state.location`" constraint. It relies on the LLM to self-correct, which fails in T7.
- Token usage is stable (~1300-1500 tok_in). No obvious bloat.

### Mechanic Placement
- `intent_verb` mapping is correctly placed in rules. However, the validation step should catch target mismatches before dice resolution.

### Issues
- **Target hallucination** (turns: 7) — Failure mode: `scope/domain mismatch`. Remediation: Add a strict validation rule in the rules prompt: `target MUST be an ID or name from the provided present_npcs list. If the player's intent references an absent entity, set target to the nearest present NPC or "none" and note the mismatch in stakes.`
- **Intent verb on absurd actions** (turns: 9) — Failure mode: `bad prompt`. Remediation: Add a fallback directive: `If the target is inanimate or the action is physically nonsensical, set intent_verb to "interact" or "sneak" and set check.required=false unless the fiction implies a social/mental check.`

### Pipeline Score (1-5)
**4**

## Pipeline: narrate
### Trace
**Turn 3:** Narrator receives `partial` directive, `gm_beat` (revelation), and `active_domains`. Outputs prose integrating Halden's nervousness, the satchel handoff, and the hooded figures. Emits `<scope>{"active_domains":["scene","location_change","inventory","pc_condition","quest_updates","recent_events","compendium_npc"]}</scope>`.
**Turn 8:** Narrator receives `success` directive, `breathing_room` gm_beat, `deescalate=true`. Outputs prose of the key turning, door opening, and thugs being shut out. Scope correctly flags `location_change` and `scene`.

### What Went Well
- Prose quality is exceptional. It adheres strictly to the `eval-pack` style: second-person past tense, concrete sensory details, no archaic phrasing, and appropriate word count.
- Dice-band binding is perfect. `Partial` results consistently introduce a complication (toughs demand more, satchel grabbed) without negating the player's intent. `Success` results provide clean resolution with breathing room.
- GM beat integration is seamless. The narrator treats the backstage instruction as fiction, never breaking the fourth wall.

### What Went Poorly
- **Scope over-flagging:** The narrator frequently flags `pc_condition` and `inventory` even when no change occurs (e.g., T4, T8). While the prompt says "bias towards inclusion," this forces extractors to run unnecessarily, wasting tokens and increasing parse risk.
- **Narrative redirection:** In T7, the player's input references Halden, but the narrator correctly ignores it and focuses on the toughs. This is good fiction, but the prompt's "Player intent is truth" rule conflicts slightly with scene reality. The narrator handles it well, but the prompt should explicitly prioritize `present_npcs` over player intent when they conflict.

### Prompt Analysis
- The narrate prompt is dense but well-structured. The `Active scope tail` instructions are clear.
- Redundancy: The `Known Characters` and `NPCs Present in Scene` sections are repeated verbatim in every turn's prompt. This is necessary for grounding but contributes to token bloat.

### Mechanic Placement
- `gm_beat` consumption is correctly placed in narrate. It clears the pending beat and integrates it naturally.
- Scope tail generation belongs here. It works well.

### Issues
- **Scope bias causing unnecessary extractor runs** (turns: 4, 8, 9) — Failure mode: `wasted tokens`. Remediation: Tighten the scope instruction: `Only flag inventory or pc_condition if the narration explicitly confirms a gain, loss, or condition change. Do not flag them for mere mentions or environmental descriptions.`

### Pipeline Score (1-5)
**5**

## Pipeline: extract_scene
### Trace
**Turn 3:** Extracts `location_change` to `marrows_crossing_center`, `npc_add` for hooded figures, `scene_pressure_add` for satchel target, `gm_beat` (revelation).
**Turn 8:** Extracts `location_change` to `crossed_keys_inn_entrance` (same ID as T7), `npc_remove` for toughs, `scene_pressure_remove` for `road_tax_confrontation`.

### What Went Well
- NPC lifecycle management is robust. `npc_add`, `npc_remove`, and `npc_update` are used correctly based on narration presence.
- Scene pressure tracking is excellent. Pressures escalate (`background` → `building` → `immediate`) and are correctly removed when the fiction resolves them (T8).
- GM beat generation is consistent and follows the instruction rules (specific entities, concrete instructions).

### What Went Poorly
- **Location change scope mismatch:** In T8, the extractor emits `location_change` with ID `crossed_keys_inn_entrance`, which is identical to the previous turn's location ID. The auto-checker correctly flags this as a failure to change state. The extractor should only emit `location_change` when the `id` changes, or the engine should handle description updates separately.
- **Compendium NPC matching:** In T5, the extractor adds `scarred_tough` and `bald_tough` as new NPCs, but the compendium already contains `tough_a` and `tough_b` with matching bios. The extractor fails to match descriptors to existing compendium entries, creating duplicate identities.

### Prompt Analysis
- The NPC match instruction is detailed but the LLM consistently ignores the compendium pre-check. The prompt needs a stronger directive: `If the narration describes an NPC matching a compendium bio or alias, use the existing ID. Do not create new IDs.`
- Location description checklist is good, but the `location_change` emission rule lacks an ID-change guard.

### Mechanic Placement
- `gm_beat` extraction belongs here. It works well.
- `scene_pressure` lifecycle belongs here. It works well.

### Issues
- **Duplicate compendium NPC creation** (turns: 5, 7) — Failure mode: `schema drift`. Remediation: Add a hard constraint in the extract_scene prompt: `Compare narration descriptors against compendium.npcs. If a match exists, emit npc_update with the existing ID. Never emit npc_add for known compendium entries.`
- **Location change ID mismatch** (turns: 8, 9) — Failure mode: `scope/domain mismatch`. Remediation: Add rule: `Emit location_change ONLY if the new location ID differs from state.location.id. If only the description changes, set location_change to null.`

### Pipeline Score (1-5)
**3**

## Pipeline: extract_state
### Trace
**Turn 3:** Extracts `inventory_add` for `heavy_satchel`, `inventory_remove` for `credits` (200).
**Turn 6:** Extracts `inventory_remove` for `credits` (200), `pc_condition_add` for `compromised`.
**Turn 7:** Extracts `pc_condition_add` for `bruised_ribs`. Applied deltas show `pc_condition_add: []` (silently dropped).

### What Went Well
- Inventory delta accuracy is high. Items are correctly added/removed with proper IDs and amounts.
- Condition guidance tied to roll context works well. `shaken` added on fail, `compromised` added on partial.

### What Went Poorly
- **Silent condition duplication:** In T7, the extractor outputs `pc_condition_add` for `bruised_ribs`, which already exists. The applied deltas show an empty array for conditions, and rejected deltas are empty. The validator silently drops it, but the extractor should have checked for existence or the engine should dedup. This creates a disconnect between extraction and application.
- **Generic item mapping:** The prompt's generic mapping rule is followed, but the extractor sometimes infers amounts loosely (e.g., "heavy satchel" → amount 1, which is fine, but could be tighter).

### Prompt Analysis
- The deduplication rule is present but ignored by the LLM. The prompt should explicitly state: `Check active_conditions before emitting pc_condition_add. If the ID exists, emit nothing or emit pc_condition_update if severity changes.`
- Token usage is stable.

### Mechanic Placement
- Inventory extraction belongs here. Correct.
- Condition extraction belongs here. Correct.

### Issues
- **Condition duplication and silent drop** (turns: 7, 9) — Failure mode: `failed to output key information`. Remediation: Add a pre-check directive in the extract_state prompt: `Compare proposed condition IDs against active_conditions. If an ID already exists, set pc_condition_add to null for that ID. Do not emit duplicates.`

### Pipeline Score (1-5)
**3**

## Pipeline: extract_progress
### Trace
**Turn 1:** Marks `settle_the_debt` objective 1 done.
**Turn 2:** Marks objective 2 done. Quest auto-completes.
**Turn 3:** Marks `deliver_the_ledger` objective 1 done. Adds recent event.
**Turn 5:** Adds recent event for toughs. Does not mark quest objectives (correct, as no contact was made).

### What Went Well
- Quest objective completion logic is accurate. The "Contact and meet" rule is correctly applied (T1, T3).
- Recent events are added judiciously, avoiding restatement of known facts.
- Action suggestions are relevant and grounded in the current scene/quest state.

### What Went Poorly
- **Intent grounding:** In T7, the progress extractor outputs `intent: persuade Halden`, mirroring the rules pipeline's hallucination. The progress extractor receives `player_intent` from the rules prompt, so it inherits the error. It should cross-reference with `present_npcs` or `recent_events` to ground the intent.
- **Compaction failure impact:** The compactor fails to generate bullets after T6, which means `recent_events` grows unbounded. The progress extractor should be more aggressive at culling or archiving events, or the compactor prompt needs fixing.

### Prompt Analysis
- The progress prompt is well-structured. The quest deduplication rule is clear.
- The `recent_events_add` guidance is good, but the ring buffer limit (max 15) isn't enforced by the extractor; it's an engine limit. The extractor should be told to prioritize events.

### Mechanic Placement
- Quest updates belong here. Correct.
- Recent events belong here. Correct.
- Action suggestions belong here. Correct.

### Issues
- **Inherited intent hallucination** (turns: 7, 9) — Failure mode: `failed to input key information`. Remediation: Pass `present_npcs` directly to the progress prompt's intent grounding section, or instruct the extractor to override `player_intent` if it references absent entities.
- **Recent event bloat** (turns: 7-10) — Failure mode: `wasted tokens`. Remediation: Add a directive: `Limit recent_events_add to 1-2 per turn. Prioritize events that change quest status, introduce new threats, or reveal NPC allegiances. Omit redundant tracking events.`

### Pipeline Score (1-5)
**3**

# Storytelling Design Critique

## Criterion: quest_arc_quality
**Score:** 4
Quests form a clear, compelling arc. "Settle the Old Debt" resolves satisfyingly in T2, creating a clean break. "Deliver Halden's Ledger" escalates naturally from a simple courier job to a high-stakes confrontation with road toughs. The progression feels earned, and completing objectives creates meaningful narrative consequences (e.g., paying Caron frees Aren to take the ledger job, but attracts unwanted attention).

## Criterion: rewards_and_consequences
**Score:** 4
The game excels at meaningful trade-offs. Partial successes (T3, T6, T10) consistently grant the player what they want but at a cost (toughs demand more, satchel is grabbed, Matthew holds leverage). Failures (T5, T9) don't dead-end; they force creative problem-solving (using the brass key, talking to Matthew). The consequence system is tight and rewarding.

## Criterion: narrative_compellingness
**Score:** 4
The prose is consistently strong, grounding the player in a gritty, tactile world. Choices matter significantly; failing to persuade toughs forces a physical escape, which in turn triggers a new pressure at the door. The narrative maintains tension without feeling arbitrary. The only minor drag is T9, where the player's absurd input (talking to a wall) slightly breaks immersion, though the narrator handles it gracefully.

## Criterion: genre_and_universe_fit
**Score:** 5
The engine perfectly respects the "working road" genre. Tone is plain, clear, and second-person past tense. Sensory details (stale ale, mud, heavy timber, brass key) are concrete. No fantasy tropes or archaic phrasing slip through. The world feels lived-in and mechanically consistent.

## Criterion: npc_development
**Score:** 4
NPCs evolve meaningfully. Caron shifts from patient creditor to predatory lender. Halden is nervous and secretive. Edda transitions from background innkeeper to defensive ally. Matthew Estrada's military precision is consistently highlighted, building mystery. The toughs escalate from blockers to violent aggressors. All reactions feel grounded in their established roles.

## Criterion: world_consistency
**Score:** 3
Generally strong, but the auto-checker flags unsanctioned mentions (T2, T9). These are false positives (the checker misidentifies items/PC names as NPCs), but they indicate the extractor's NPC grounding could be tighter. Additionally, T7's intent hallucination (targeting Halden when he's absent) creates a brief consistency hiccup, though the narrator correctly ignores it. The compendium matching failure (T5) creates duplicate tough identities, which is a trust axis issue.

## Criterion: player_agency
**Score:** 5
The engine deeply respects player choice. Failures open new options rather than blocking progress. The player can bribe, fight, sneak, or negotiate, and the engine adapts. Even absurd inputs (T9) are narratively accommodated without breaking the game. The dice bands directly shape the fiction, giving the player meaningful control over risk and outcome.

## Criterion: consequence_persistence
**Score:** 4
Consequences carry forward well. Conditions (`bruised_ribs`, `shaken`, `compromised`) persist and affect future rolls. Scene pressures (`road_tax_confrontation`, `thugs_at_door`) escalate until resolved. The only flaw is the silent dropping of duplicate conditions, which slightly weakens the persistence tracking, but the narrative still reflects the cumulative toll.

## Criterion: pacing_and_pressure
**Score:** 4
Pressure mechanics are objective and well-tuned. Threats escalate from background rumors to immediate violence. The `deescalate` flag in T8 correctly triggers breathing room, allowing the player to catch their breath before the next crisis. Narrative pacing matches the mechanical pressure, with clear beats of tension and release.

## Criterion: momentum_arc
**Score:** 4
The session follows a clear dramatic shape: introduction (T1-2) → escalation (T3-5) → crisis (T6-7) → resolution/cliffhanger (T8-10). Momentum tracks this well, dipping on failures and recovering on successes. The final turns leave the player in a tense standoff, providing a meaningful cliffhanger rather than a flat ending.

# Prompt Redundancy Analysis

1. **narrate + progress overlap:** The `recent_events` block is duplicated verbatim in the narrate and progress prompts. This is intentional, as progress needs the full event list to update quests, but it wastes ~150-200 tokens per turn.
2. **narrate + scene overlap:** The `location` description is duplicated. This is necessary for spatial grounding in both streams.
3. **Top 3 dedup opportunities:**
   - **Recent events surface:** Replace the full `recent_events` list in the progress prompt with a compressed summary surface (e.g., "T1: Met Caron. T2: Paid debt. T3: Hired by Halden."). This saves ~100 tokens/turn without losing quest context.
   - **Known characters list:** The `Known Characters` block in the narrate prompt duplicates the compendium. Pass a smaller "scene_relevant_npcs" list instead of the full roster.
   - **Inventory cross-reference:** The inventory list is repeated in narrate, state, and progress. Pass a minimal "active_inventory_ids" surface to narrate and progress, keeping the full list only for state extraction.

# Compaction Capabilities Report

**Compaction at turn 6:**
- `bullet_named_npcs`: [OK] - Preserved Caron, Halden, Edda.
- `bullet_location`: [OK] - Preserved Crossed Keys Inn.
- `bullet_quest_outcomes`: [OK] - Noted debt settlement, ledger contract.
- `bullet_key_items`: [OK] - Noted 500 credits paid, heavy satchel gained.
- `bullet_conditions`: [FAIL] - No condition bullets generated.
- `bullet_irreversible`: [OK] - Noted debt cleared.
- `bullet_deaths`: [NA] - No deaths.
- `bullet_mech_consequences`: [OK] - Noted Caron's lingering interest.
- `bullet_culling`: [OK] - Removed atmospheric fluff, kept plot points.
- `sanitize_npc_merge`: [NA] - No duplicates.
- `sanitize_inventory`: [NA] - No duplicates.
- `sanitize_quest_close`: [FAIL] - Quest completed but not sanitized/archived.
- `sanitize_pressure`: [NA] - No pressures resolved.
- `sanitize_condition`: [NA] - No conditions cured.

**Compaction at turns 7-10:**
- All capabilities: [FAIL] - Compaction event detected but produced 0 bullets and 0 sanitization actions. The compactor prompt or logic fails to trigger after the initial compaction, leaving `recent_events` to grow unbounded and `prior_history` stagnant.

# Auto-Checker Failures

1. **Turn 2: `universal.npc_mention.extracted`**
   - **Why it failed:** The auto-checker flags "Credits", "Instead", "Voss" as names not in `npc_add/update` or known. This is a false positive. "Credits" is an inventory item, "Voss" is the PC, and "Instead" is a conjunction. The checker's NER is too broad and lacks context awareness for items/PCs.
   - **Remediation:** Update the auto-checker's exclusion list to ignore `state.pc.name`, inventory item names, and common stop words. Add a context-aware filter that checks if the mentioned word appears in the `inventory` or `pc` sections before flagging.

2. **Turn 8: `universal.location_change.applied`**
   - **Why it failed:** The extractor emits `location_change` with ID `crossed_keys_inn_entrance`, which is identical to the previous turn's location ID. The auto-checker correctly flags that the state ID didn't change, even though the description did. This is a scope mismatch in the extractor.
   - **Remediation:** Modify the extract_scene prompt to only emit `location_change` when the `id` differs from `state.location.id`. If only the description changes, set `location_change` to null and update the description via a separate field or engine logic.

3. **Turn 9: `universal.npc_mention.extracted`**
   - **Why it failed:** The auto-checker flags "Tough", "Scarred" as unsanctioned names. These are descriptors/titles, not new NPC names. The checker fails to distinguish between proper names and common nouns used as descriptors.
   - **Remediation:** Tighten the auto-checker's regex to only flag capitalized words that match the `firstname_lastname` or single-token ID format defined in the NPC ID rules. Exclude titles, descriptors, and common nouns.

# Additional Observations

- **GM Beat Lifecycle:** The GM beat system works beautifully. Beats are generated, stored in `pending_gm_beat`, consumed by the next turn's narrator, and cleared. This creates a reliable backstage storytelling loop.
- **Dice Band Integration:** The engine's handling of `partial` is its strongest mechanical feature. It consistently produces "success with complication" without breaking player agency or narrative flow.
- **Compactor Stagnation:** The compactor fires at T6 but goes dormant at T7-T10. This suggests the compactor prompt lacks a loop condition or the engine's compaction trigger logic only fires once per session. This needs immediate attention to prevent token bloat in longer runs.
- **Condition Deduplication:** The silent drop of duplicate conditions in T7/T9 indicates the Python validator is filtering them, but the extractor isn't aware. This creates a disconnect between extraction and application logs.

# Verdict

The engine demonstrates excellent mechanical design in its dice resolution, scope tailing, and GM beat lifecycle, resulting in a highly compelling and responsive narrative. The narrator consistently produces high-quality prose that respects player agency and genre constraints. However, structural flaws in the extractors (location change scope, compendium NPC matching, condition deduplication) and a compactor that fails after the first activation cap the mechanical score. The auto-checker also generates false positives due to overly broad NER. The single most important fix is to harden the extractors' grounding rules (NPC matching, location ID changes, condition deduplication) and debug the compactor's post-initial activation logic to prevent token bloat and state drift in longer sessions.

# Actionable Issues and Remediations

## Major
- **[Engine] Condition duplication and silent drop** (turns: 7, 9) — The extractor outputs duplicate conditions, which the validator silently drops. This breaks extraction logs and state tracking. **Remediation:** Add a pre-check directive in `extract_state_system.j2`: `Compare proposed condition IDs against active_conditions. If an ID already exists, set pc_condition_add to null for that ID. Do not emit duplicates.`
- **[Prompting] Compactor stagnation** (turns: 7-10) — The compactor fires at T6 but produces 0 bullets/sanitization afterward, causing `recent_events` to grow unbounded. **Remediation:** Review the compactor trigger logic in `engine.py`. Ensure it runs every N turns or when `recent_events` exceeds a threshold. Update the compactor system prompt to explicitly state: `Run this extraction every compaction cycle. If no new bullets are generated, still sanitize existing events and close completed quests.`
- **[Consistency] Location change scope mismatch** (turns: 8, 9) — Extractors emit `location_change` when only the description changes, causing auto-checker failures. **Remediation:** Update `extract_scene_system.j2`: `Emit location_change ONLY if the new location ID differs from state.location.id. If only the description changes, set location_change to null.`

## Minor
- **[Prompting] Rules target hallucination** (turns: 7, 9) — The rules extractor targets absent NPCs (Halden, wall occupants). **Remediation:** Add a strict constraint in `rules_system.j2`: `target MUST be an ID or name from the provided present_npcs list. If the player's intent references an absent entity, set target to the nearest present NPC or "none" and note the mismatch in stakes.`
- **[Prompting] Scope over-flagging** (turns: 4, 8, 9) — The narrator flags `inventory` and `pc_condition` unnecessarily, forcing extractor runs. **Remediation:** Tighten the narrate prompt's scope instructions: `Only flag inventory or pc_condition if the narration explicitly confirms a gain, loss, or condition change. Do not flag them for mere mentions or environmental descriptions.`
- **[Consistency] Compendium NPC matching failure** (turns: 5, 7) — The extractor creates duplicate IDs for known compendium NPCs (toughs). **Remediation:** Add a hard constraint in `extract_scene_system.j2`: `Compare narration descriptors against compendium.npcs. If a match exists, emit npc_update with the existing ID. Never emit npc_add for known compendium entries.`

## Trivial
- **[Auto-Checker] False positive tuning** (turns: 2, 9) — The auto-checker flags items, PC names, and descriptors as unsanctioned NPCs. **Remediation:** Update the auto-checker's exclusion list to ignore `state.pc.name`, inventory item names, and common stop words. Add a context-aware filter that checks if the mentioned word appears in the `inventory` or `pc` sections before flagging.
- **[Prompting] Recent event bloat** (turns: 7-10) — Progress extractor adds redundant events, compounding token usage. **Remediation:** Add a directive in `extract_progress_system.j2`: `Limit recent_events_add to 1-2 per turn. Prioritize events that change quest status, introduce new threats, or reveal NPC allegiances. Omit redundant tracking events.`