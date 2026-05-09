

---
mechanical_score: 3
narrative_score: 4
pipeline_scores:
  rules: 4
  narrate: 4
  extract_scene: 4
  extract_state: 3
  extract_progress: 2
---

# Mechanical Design Critique

## Pipeline: rules
**Trace**
- Turn 2: Input `Walk over to Caron's table...` → LLM outputs `intent: negotiate`, `skill: charisma`, `difficulty: normal`, `required: true`. Python rolls 2d6+3+1=6 → FAIL. Directive shapes narrator to dismiss the attempt.
- Turn 9: Input `I pull out the brass key...` → LLM outputs `intent: hack`, `skill: dexterity`, `difficulty: easy`, `required: true`. Python rolls 2d6+3+1=10 → SUCCESS.
- Turn 10: Input `I press my ear against the wall...` → LLM outputs `intent: persuade`, `skill: charisma`, `difficulty: normal`, `required: true`. Python rolls 2d6+3=6 → FAIL.

**What Went Well**
Intent classification accurately maps player actions to mechanical checks. The anti-declare-outcome rule is respected; even when the player phrases actions as definitive ("I unlock the door"), the engine still rolls (Turn 9) and narrates the mechanical result. Dice resolution correctly applies stat mods and condition mods, and the `directive` field reliably gates the narrator's creative latitude (e.g., Turn 2 FAIL directive forces Caron to dismiss the negotiation rather than accept it).

**What Went Poorly**
The `intent_verb` selection occasionally drifts from the prescribed list or feels mismatched to the skill. In Turn 9, the verb is `hack` for using a physical key, which is acceptable but borders on scope creep for a lockpicking skill. More critically, Turn 10 classifies whispering at a wall and offering a coin as `persuade` with `required: true`. The prompt's decision rule says to set `required=false` for idle observation or casual conversation, but whispering at a wall is arguably unimpeded movement or a failed social attempt that shouldn't consume a turn's mechanical weight. The rules pipeline lacks a clear filter for "futile actions" that should auto-fail or skip rolling.

**Prompt Analysis**
The rules prompt is concise and well-structured. However, the `intent_verb` list could benefit from explicit fallback instructions when the action is purely environmental (e.g., `explore`, `interact`). The prompt successfully enforces the anti-declare-outcome rule, preventing the LLM from pre-rolling successes.

**Mechanic Placement**
Intent classification and dice resolution correctly live in Step 0. The `directive` output properly feeds Step 1. No misplaced mechanics detected.

**Issues**
- **Futile action rolling** (Turns 2, 10) — Failure mode: `scope/domain mismatch`. The engine rolls for actions that narratively should auto-fail or be skipped (whispering at a wall). Remediation: Add a prompt rule: "If the target of the action is inanimate, absent, or clearly unresponsive, set `check.required=false` and `intent_verb=interact`."
- **Verb list rigidity** (Turn 9) — Failure mode: `scope/domain mismatch`. `hack` is used for a physical key. Remediation: Expand `intent_verb` list to include `unlock` or `pick_lock`, or instruct the LLM to map physical manipulation to `dexterity` without forcing `hack`.

**Pipeline Score (4/5)**

## Pipeline: narrate
**Trace**
- Turn 2: Receives FAIL directive. Narrates Caron dismissing Aren, demanding full payment by sunrise. Matches band.
- Turn 6: Receives SETBACK directive. Narrates toughs demanding a toll and flanking. Matches band.
- Turn 9: Receives SUCCESS directive. Narrates the lock yielding smoothly. Matches band.

**What Went Well**
The narrator strictly honors dice bands and directives. Failures result in narrative costs (dismissal, extortion) rather than dead ends. The prose adheres to the "plain, clear" register, using concrete sensory details ("screech of legs", "heavy clink of coins"). GM beats from previous turns are integrated naturally (Turn 3 shadows, Turn 5 tavern doorway, Turn 10 parchment).

**What Went Poorly**
There is a direct contradiction between the `World Pack Style` (which mandates "second-person past-tense") and the `Narrate System Prompt` (which mandates "Second person, present tense"). The engine outputs present tense throughout. While the prompt wins, this creates a friction point for pack authors. Additionally, Turn 10's narration describes pulling "a single coin from your pouch," but the state extractor removes the entire `leather_pouch` item. The narrator should have specified "a single coin from your leather pouch" to allow accurate state tracking.

**Prompt Analysis**
The narrate prompt is heavy with constraints (pacing, items, NPCs, markdown). The `active scope tail` instruction works well to gate downstream extractors. Token usage grows steadily (~2800 → ~6800), indicating the prompt isn't being aggressively trimmed, which is fine for quality but risks context overflow later.

**Mechanic Placement**
GM beat consumption correctly happens in Step 1. Scope tail emission correctly gates Steps 2a/2b/2c. No misplaced mechanics.

**Issues**
- **Tense mismatch with style guide** (All turns) — Failure mode: `scope/domain mismatch`. Style.md says past, prompt says present. Remediation: Align `narrate_system.j2` with `style.md` or explicitly override it in the prompt with a clear precedence rule.
- **Partial item consumption phrasing** (Turn 10) — Failure mode: `failed to output key information`. Narration says "single coin from your pouch," causing state extractor to remove the whole stack. Remediation: Instruct narrator to specify exact item names when spending: "pull a single coin from your **leather_pouch**."

**Pipeline Score (4/5)**

## Pipeline: extract_scene
**Trace**
- Turn 2: Extracts `caron_debt_deadline` (building pressure) and `gm_beat` (complication).
- Turn 6: Extracts `tough_extortion` (immediate pressure) and updates NPC notes for toughs.
- Turn 9: Extracts `location_change` to `inn_service_corridor` and removes `caron_debt_deadline` pressure.

**What Went Well**
Scene extraction accurately tracks NPC presence, location changes, and pressure lifecycle. The de-escalation flag in Turn 9 correctly triggers pressure removal. NPC updates are precise, capturing shifting notes without hallucinating new identities. GM beat generation follows the schema and provides actionable, entity-specific instructions.

**What Went Poorly**
Turn 6 adds `tough_a` and `tough_b` to `npc_update` but fails to add them to `npc_add` initially, relying on compendium matching. This works but risks ID drift if the compendium isn't perfectly synced. The prompt's NPC ID rules are strict (`firstname_lastname`), but the engine uses `tough_a`/`tough_b` from the seed state, which is fine for testing but would break in production without aliasing.

**Prompt Analysis**
The scene prompt is comprehensive. The NPC match instruction and compendium checklist are excellent safeguards. Token usage is high (~3600-4200) due to passing full compendium and recent events, but duplication is intentional per design.

**Mechanic Placement**
GM beat generation correctly lives in Step 2a. Pressure lifecycle management is properly scoped to scene. No misplaced mechanics.

**Issues**
- **Compendium ID rigidity** (Turn 6) — Failure mode: `schema drift`. Engine uses `tough_a`/`tough_b` instead of generated IDs. Remediation: Instruct scene extractor to generate IDs from the name pool if compendium IDs are placeholders, or ensure seed state uses canonical IDs.

**Pipeline Score (4/5)**

## Pipeline: extract_state
**Trace**
- Turn 3: Adds `stained_ledger`, removes `credits` (500).
- Turn 4: Adds `credits` (200).
- Turn 7: Removes `credits` (200), adds `compromised` condition.
- Turn 10: Adds `stained_parchment`, removes `leather_pouch` (full stack).

**What Went Well**
Inventory delta accuracy is generally high. The extractor correctly matches existing IDs (`credits`) and handles stack updates. Condition lifecycle works well; `compromised` is added in Turn 7 based on the setback narrative, and the prompt's condition guidance correctly ties roll context to condition types.

**What Went Poorly**
Turn 10 is a critical failure: the narration says "pull a single coin from your pouch," but the extractor removes the entire `leather_pouch` item (`amount: 1` full stack). The prompt says "Never emit amount greater than the current stack," but fails to instruct the LLM to handle partial consumption explicitly. This breaks inventory tracking.

**Prompt Analysis**
The state prompt has strong match instructions and hard caps. However, it lacks explicit guidance for partial item consumption (e.g., "If the player spends part of a stack, emit `inventory_remove` with the exact amount spent, or `inventory_update` to reduce the stack").

**Mechanic Placement**
Inventory and condition extraction correctly live in Step 2b. Cross-stream handoff (`items_gained`/`items_lost`) is minimal but functional. No misplaced mechanics.

**Issues**
- **Full stack removal on partial spend** (Turn 10) — Failure mode: `failed to output key information`. Extractor removes entire `leather_pouch` instead of 1 coin. Remediation: Add prompt rule: "If narration implies partial consumption of a stack, emit `inventory_remove` with the exact amount spent. Do not remove the entire item unless the narration states the stack is exhausted."

**Pipeline Score (3/5)**

## Pipeline: extract_progress
**Trace**
- Turn 2: Adds `caron_ultimatum` event.
- Turn 4: Marks `deliver_the_ledger` objective 1 as done.
- Turn 6: Adds `toll_extortion_attempt` event. Hallucinates new quest `deliver_stained_ledger` with empty objectives.
- Turn 8: Marks `deliver_the_ledger` objective 2 as done.
- Turn 10: Adds `merchant_seal_connection` event.

**What Went Well**
Quest objective completion logic works correctly when triggered by explicit narration or success bands. Recent events tracking provides a solid narrative history. Action suggestions are generally relevant to current quests and scene state.

**What Went Poorly**
Turn 6 hallucinates a new quest `deliver_stained_ledger` despite the prompt explicitly stating "Bar is HIGH — only start a new quest for a major new obligation." This is a prompt adherence failure. More critically, the prompt schema hardcodes `turn: 0` in the example JSON for `recent_events_add`. The auto-checker expects the actual turn number, causing repeated failures across Turns 2, 3, and 4.

**Prompt Analysis**
The progress prompt is bloated with redundant `recent_events` and `active_quests` blocks that duplicate what's already in the state. The `turn: 0` schema bug is a critical prompt defect. The "Contact and meet objective rule" is well-defined but not heavily utilized in this trace.

**Mechanic Placement**
Quest updates and recent events correctly live in Step 2c. However, the quest hallucination suggests the prompt's threshold guidance is too weak or the LLM is over-indexing on item mentions.

**Issues**
- **Hardcoded turn: 0 in schema** (Turns 2, 3, 4) — Failure mode: `bad prompt`. Schema example forces LLM to output `turn: 0`, breaking auto-checker. Remediation: Change schema example to `turn: <current_turn>` or remove the field from the example and instruct LLM to use the turn number from the prompt header.
- **Quest hallucination** (Turn 6) — Failure mode: `misplaced mechanic`. Adds quest for an item. Remediation: Strengthen prompt constraint: "Do NOT create quests for inventory items, minor discoveries, or environmental observations. Only create quests for explicit NPC contracts, faction obligations, or major plot hooks."

**Pipeline Score (2/5)**

# Storytelling Design Critique

## quest_arc_quality
**Score: 3**
Quests advance logically (Turn 4 accepts contract, Turn 8 delivers ledger), but the engine hallucinates a new quest in Turn 6 (`deliver_stained_ledger`) with no objectives, breaking immersion. The primary debt quest stalls until Turn 3, then hits a wall when Caron refuses full payment. The ledger quest resolves cleanly, but the stalled debt quest leaves the player in a loop.

## rewards_and_consequences
**Score: 4**
Consequences are meaningful: failing to negotiate (Turn 2) leads to a deadline; failing the bribe (Turn 7) escalates to extortion and adds a `compromised` condition. Rewards are tangible: Turn 4 grants 200 credits, Turn 8 grants a leather pouch. Trade-offs feel earned.

## narrative_compellingness
**Score: 4**
The tension between Aren's desperation and Caron's rigidity drives the early turns well. The toughs' extortion adds immediate stakes. Turn 10's absurdity (whispering at a wall, offering a coin) is funny but fits the desperate PC archetype. Choices matter; failing a bribe opens new complications rather than dead ends.

## genre_and_universe_fit
**Score: 4**
The gritty merchant road tone is consistent. NPC interactions feel grounded in a working economy (credits, tolls, interest). The prose avoids fantasy tropes, sticking to concrete details. The only minor dip is the wall-whispering, which borders on slapstick, but it's forgivable given the PC's state.

## npc_development
**Score: 3**
Caron and Halden react consistently to player actions, but their arcs are static. Matthew Estrada appears in Turn 11 but isn't integrated into scene state (extract scene skipped), so his presence doesn't affect future turns. NPCs feel like reactive props rather than evolving agents.

## player_agency
**Score: 4**
The engine respects player choice. Failing a persuasion check doesn't lock the player out; it changes the terms (Turn 6 toll, Turn 7 escalation). The suggested actions in Turn 11 offer distinct avenues (press, charm, scan, release), maintaining agency.

## pacing_and_pressure
**Score: 4**
Pressure escalates naturally: deadline (Turn 2) → toll (Turn 6) → extortion (Turn 7) → revelation (Turn 9). Breathing room is provided in Turn 9 (corridor escape). Momentum tracks struggle well, dipping to -2 in Turn 6 before recovering. Pacing feels tight without feeling rushed.

# Prompt Redundancy Analysis

The `## Prompt Redundancy` block shows significant overlap between `narrate` and `progress` (9 blocks) and `narrate` and `scene` (2 blocks).

1. **Is the duplication intentional?** Yes, per design, the narration feeds all three extractors. However, the `recent_events` list is passed to the narrator, then the narrator's output (which repeats events) is passed to the progress extractor. This is redundant.
2. **Which pipeline should own it?** The `recent_events` list should be owned by the state/context loader and passed directly to extractors. The narrator should only receive `chronicle_tail` (compressed history) to avoid regurgitating events that the progress extractor already has.
3. **Token waste estimate:** ~3 lines × ~60 chars × 9 blocks ≈ 1620 chars/turn wasted across streams. Over 10 turns, that's ~16k tokens.

**Top 3 dedup opportunities:**
- **Remove `recent_events` from narrate prompt:** Pass only `chronicle_tail` to narrator. Progress extractor already receives `recent_events` directly from state.
- **Streamline `active_quests` passing:** Pass a compressed quest summary to all extractors instead of full objective lists. Use IDs + status flags.
- **Deduplicate `location`/`world_state` blocks:** These are repeated in narrate, scene, and state prompts. Pass a single `world_context` surface that all streams reference.

# Compaction Capabilities Report

- `[NA]` Compaction did not fire during this run (run length < `compact_every` threshold). No per-capability evaluation possible. Note: Token counts grow steadily (~2800 → ~6800), suggesting compaction will be necessary around Turn 15-20 to prevent context overflow.

# Auto-Checker Failures

1. **`universal.recent_events_add.turn_stamped` (Turns 2, 3, 4)**
   - **WHY:** The `extract_progress_system.j2` prompt schema hardcodes `turn: 0` in the example JSON for `recent_events_add`. The LLM copies this pattern, outputting `turn: 0` instead of the actual turn number.
   - **Remediation:** Update the prompt schema example to `turn: <current_turn>` or explicitly instruct: "Set `turn` to the current turn number provided in the prompt header."

2. **`universal.npc_mention.extracted` (Turns 2, 3, 6, 9, 10, 11)**
   - **WHY:** The auto-checker flags capitalized words in narration (e.g., "Voss", "Credits", "Take", "Instead", "Ignoring", "Brass", "Your", "Open", "Who") as unextracted NPC names. These are either the PC, inventory items, or sentence starters. The scene extractor correctly ignores them, but the auto-checker's validation logic is too aggressive.
   - **Remediation:** Update the scene prompt to explicitly exclude terms: "Do NOT extract the PC's name, inventory items, or common words capitalized at the start of sentences as NPCs. Only extract genuinely new named characters." Also, consider relaxing the auto-checker to ignore PC names and sentence starters.

# Additional Observations

- **Tense Contradiction:** `World Pack Style` mandates past-tense, but `Narrate System Prompt` mandates present-tense. The engine outputs present tense. This creates friction for pack authors and should be resolved in the prompt layer.
- **GM Beat Integration:** The engine successfully consumes GM beats from previous turns (Turn 2 beat → Turn 3 shadows, Turn 4 beat → Turn 5 doorway, Turn 9 beat → Turn 10 parchment). This shows the backstage instruction pipeline works as designed.
- **Momentum Tracking:** Momentum correctly dips to -2 on setbacks (Turn 6) and recovers on successes (Turn 8, Turn 9). The engine uses momentum to influence GM beat type (complication vs opportunity), which is functioning well.
- **Inventory ID Normalization:** The engine handles ID normalization well (e.g., `credits` vs `Credits`), but the partial consumption bug in Turn 10 shows a gap in amount inference logic.

# Verdict

The engine demonstrates strong mechanical design in intent classification, dice resolution, and GM beat integration, but suffers from two critical prompt defects: a hardcoded `turn: 0` schema bug in the progress extractor and a state extractor that fails to handle partial inventory consumption. These cause auto-checker failures and inventory drift. Narrative quality is high, with meaningful consequences and tight pacing, though NPC development remains reactive. The single most important fix is to correct the `extract_progress` prompt schema to output actual turn numbers and add explicit partial-consumption instructions to the `extract_state` prompt.

# Narrative Recap

Aren Voss arrives in Marrow's Crossing to settle a 500-credit debt with Caron, only to be dismissed with a harsh sunrise deadline. He accepts a courier contract from Halden to deliver a ledger for 200 credits, earning enough to cover the interest but not the principal. En route to the inn, he's intercepted by Caron's thugs who escalate to extortion. After delivering the ledger and securing a payment pouch, Aren discovers a mysterious parchment in the service corridor linking the ledger to hidden payments. He confronts a suspicious military-minded traveler, Matthew Estrada, revealing a web of intrigue surrounding the town's merchant road.