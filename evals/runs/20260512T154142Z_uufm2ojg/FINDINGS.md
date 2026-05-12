# Eval Findings — Run 20260512T154142Z_uufm2ojg

Consolidated findings from both judge reports, categorized by concern and type.

---

## 1. Prompt Quality

### 1.1 Rules: Spurious rolls on movement and social initiation
**Type:** Bad prompt — missing examples  
**Turns:** T1, T12  
Walking over to a table and sitting down, or grabbing an item from your coat and sprinting, are unimpeded movement. The rules prompt has the no-roll rule in prose but no few-shot examples. The model rolls on pure approach-and-sit and movement-plus-retrieval. Adding concrete no-roll examples for these patterns would eliminate the false positives.

### 1.2 Rules: Spurious roll on commercial transaction with willing NPC
**Type:** Bad prompt — ambiguous exception  
**Turns:** T3  
Halden is offering the courier job (willing merchant); Aren is naming a price. The payment exception rule exists in prose but is wordy and not converted to a concrete example. The model rolls charisma/normal when it should emit `required=false`.

### 1.3 Narrate: Fail band played as partial outcome
**Type:** Bad prompt — ambiguous band directive  
**Turns:** T1, T3  
On `fail` bands, the narration describes Caron engaging constructively (spreading a parchment, demanding proof) and Halden counter-offering a split payment. Both read as `partial` outcomes, not outright failures. The fail band directive needs a sentence explicitly prohibiting constructive NPC engagement.

### 1.4 Narrate: Pressure directive absent from user prompt
**Type:** Failed to input key information  
**Turns:** T8, T10, T12  
Two immediate pressures active but the Pressure/Overwhelm directive is missing from the narrate user prompt. This is a state-read ordering issue — the narrate prompt builder may not be injecting the directive when there are 2+ immediates, or pressures weren't committed to state before the narrate call.

### 1.5 Narrate: Pressure directive ignored when present
**Type:** Bad prompt — model not following instruction  
**Turns:** T1, T8, T10, T12  
Even when the pressure directive IS in the user prompt, the LLM ignores it in prose. Needs an explicit weaving instruction: "Weave the exact text from the Pressure directive into the opening 2-3 sentences."

### 1.6 Extract State: Missing key-use extraction
**Type:** Bad prompt — missing few-shot  
**Turns:** T8  
The brass key is used to unlock a door, narration confirms the key works, but `inventory_remove[brass_key]` is not emitted. The prompt has six payment examples but zero physical-consumption examples. Adding a key-use few-shot would prevent this.

### 1.7 Extract State: Missing inventory_add for NPC-given items
**Type:** Bad prompt — missing few-shot  
**Turns:** T3  
Halden offers 100 credits as a split payment. Narration describes the player accepting the pouch, but `inventory_add[credits, 100]` is not emitted. Adding an "NPC hands you a pouch" few-shot example would prevent this.

### 1.8 Extract State: Missing inventory_remove for vague spending
**Type:** Bad prompt — ambiguous rule  
**Turns:** T13  
Player pays a dock boy. The spending rule mandates `inventory_remove` even for vague amounts, but the extractor emits nothing. The rule and six payment examples cover named amounts but not vague/implicit spending.

### 1.9 Extract Progress: Completed quest emission causing ID collisions
**Type:** Bad prompt — model not following dedup rule  
**Turns:** T2, T7  
The `quest_deduplication (MANDATORY)` rule exists in the system prompt but the model re-emits `settle_the_debt` and `deliver_the_ledger` with `status: active` after they just completed. Adding a NEVER few-shot example showing what NOT to do when a quest just completed would prevent this pattern.

### 1.10 Extract Progress: Contradictory auto-close vs dedup rules
**Type:** Bad prompt — internal contradiction  
The auto-close rule says "emit quest with objectives done" while the dedup rule says "do not emit if new state matches existing." These contradict. The model follows neither correctly.

### 1.11 Extract Scene: Missing standoff/confrontation scene tags
**Type:** Failed to output key information  
**Turns:** T5  
Player confronts two armed toughs blocking a door. The scene extractor should have tagged `standoff` or `intimidation` at minimum. Adding examples for standoff/confrontation scene tags would prevent this.

### 1.12 Cross-prompt redundancy: PC stats duplicated across all 5 prompts
**Type:** Wasted tokens  
**Impact:** ~780 tokens/run  
PC stats appear verbatim in all 5 pipeline user prompts. Rules and narrate need them; scene/state/progress extractors do not. Removing from extract_scene alone saves ~60 tokens/turn.

### 1.13 Cross-prompt redundancy: NPC bios duplicated in present_npcs + known_characters
**Type:** Wasted tokens  
**Impact:** ~1560 tokens/run  
Same NPC bio appears in both `present_npcs` and `known_characters` in the scene user prompt. `present_npcs` should only carry `id`, `name`, `notes`.

### 1.14 Cross-prompt redundancy: Full narrative duplicated in progress prompt
**Type:** Wasted tokens  
**Impact:** ~2600 tokens/run  
Both `last_turn_narration` and current narration appear in full in the progress user prompt. Compressing `last_turn_narration` to a 3-sentence summary would save tokens at scale.

### 1.15 Rules: Intent verb mapping needs few-shot examples
**Type:** Bad prompt — missing examples  
Edge cases like `deceive` vs `persuade` for bribes, `sneak` for lockpicking, would benefit from 2-3 few-shot examples in the rules system prompt.

### 1.16 Rules: Compound actions and anti-declare-outcome sections overlap
**Type:** Bad prompt — redundant sections  
Both sections are present and don't contradict, but a model may apply both to the same input ambiguously. Trimming the compound actions section would reduce confusion surface.

---

## 2. State Fidelity

### 2.1 Delta validation failures
**Type:** Engine logic — overdraw clamp  
**Turns:** T9, T13  
T9: Extractor emits `inventory_remove[credits, 1]` but inventory has 0 credits. T13: Narration invents a shirt not in inventory, extractor faithfully extracts the remove, causing rejection. The state extractor needs a rule: "If narration implies spending but inventory amount is 0, omit or flag as failed."

### 2.2 Phantom inventory item: brass_key persists after use
**Type:** Extraction drift  
**Turns:** T8–T13  
Brass key used to open a door at T8 but never removed from inventory. Remains as a phantom item through the end of the run.

### 2.3 Quest auto-close failure: deliver_the_ledger stays active
**Type:** Extraction drift  
**Turns:** T7  
All objectives marked done but the progress extractor re-emits the quest with `status: active`, preventing the engine from recognizing the all-done condition and auto-closing.

### 2.4 Condition not resolved after physical success
**Type:** Extraction drift  
**Turns:** T8–T13  
`bruised_ribs` persists all 13 turns. Player tackles someone physically at T8 (strength-based combat) — a reasonable expectation of a condition callback or removal. The extractor isn't removing resolving conditions aggressively enough.

### 2.5 Ghost NPCs: toughs removed then re-added
**Type:** Extraction drift + narration drift  
**Turns:** T7, T10  
Scene extractor erroneously removes toughs at T7 (`npc_remove`). Narration at T10 says they were "hovering near the door." State re-adds them as `npc_add`, creating ghost NPCs.

### 2.6 Duplicate quest creation: deliver_halden_ledger
**Type:** Extraction drift  
**Turns:** T8  
Progress extractor creates `deliver_halden_ledger` as a semantic duplicate of `deliver_the_ledger`. The dedup rule should check against `state.quests` not just `active_quests`.

### 2.7 Inventory item re-added as new instead of update
**Type:** Extraction drift  
**Turns:** T8  
Brass key should have been `inventory_update` or retained, not re-added as a new ID.

---

## 3. System Cohesion

### 3.1 Compaction sanitization entirely absent
**Type:** Bad prompt — missing sanitization steps  
**Turns:** T6, T12  
Chronicle bullets are accurate but `quest_close`, `condition_remove`, `pressure_remove`, and `inventory_remove` sanitization steps are not executed by the compactor. The compactor system prompt needs explicit sanitization steps after bullet generation.

### 3.2 Pressure overlong and inert
**Type:** Design — missing TTL/escalation  
**Turns:** T3–T13  
`road_surveillance` (11 turns) and `road_ambush_threat` (10 turns) sit inert for 9-10 turns. Recommend capping ambient pressures at 4 turns then forcing escalation or resolution via beat.

### 3.3 Pressure urgency overclassification
**Type:** Design — urgency calibration  
**Turns:** T1  
`caron_impatience` uses `urgency: immediate` for a social/commercial standoff. A first-turn debt conversation at normal difficulty warranted `building` urgency at most.

### 3.4 Unresolved immediate pressures at run end
**Type:** Design — terminal state handling  
**Turns:** T9, T10  
Two immediate pressures persist unresolved through T13. If this is the final turn, they should have been resolved or explicitly failed.

### 3.5 Beat type variety low
**Type:** Design — beat generation skew  
Beats are heavily skewed toward `pressure` (5/6). `revelation` used once. The progress extractor may be over-generating beats during high-pressure phases rather than exercising `null` when appropriate.

### 3.6 Orphaned beat at run end
**Type:** Expected — run termination  
**Turns:** T13  
Beat generated at T13 with no subsequent turn to surface it. Expected behavior at run end.

### 3.7 Incomplete quest close: clear_the_road_toughs
**Type:** Extraction drift  
**Turns:** T6–T13  
Quest advanced at T6 but not fully closed. Quest objective resolution appears incomplete.

### 3.8 Momentum observability gap
**Type:** Observability — diff suppression  
**Turns:** T2–T13  
Momentum field present in T1 snapshot (`momentum: -1`) but never surfaced in subsequent diffs. Either the state differ suppresses unchanged-value outputs, or momentum stopped updating after T1.

### 3.9 Directive conflict: momentum tone vs band tone
**Type:** Design — unresolved tension  
**Turns:** T3  
Momentum at -2 (LOW) with directive to "find the one thing going slightly in their favor." The fail band directive says negotiation fails. The model chose momentum over band — right for story cohesion but technically a P8 violation. The engine should reconcile this conflict in the prompt.

### 3.10 Pacing: consecutive immediate-pressure turns
**Type:** Design — approaching burnout  
**Turns:** T9–T11  
Three consecutive immediate-pressure turns (toughs discovered, Matthew Estrada confrontation, combat). Approaching burnout threshold.

---

## 4. Auto-Checker Issues

### 4.1 NPC name extraction false positives
**Type:** Auto-checker noise — scope/domain mismatch  
**Turns:** T2, T4, T5, T6, T7, T8, T9  
Checker flags capitalized words like "Slowly", "Marrow", "Crossed", "Ledger", "Inside", "Outside", "Beyond" as NPCs. These are adverbs, location names, and object nouns. The checker should only flag proper nouns matching `known_characters` or `present_npcs` IDs.

### 4.2 Pressure directive rendering timing bug
**Type:** Auto-checker noise — false positive  
**Turns:** T1, T8  
Pressure added late in a turn's progress run but the checker tests the current turn's narrate prompt for it. The pressure won't appear in narrate until the NEXT turn. The checker should only flag `pressure_directive_rendered` when the pressure existed in the prior turn's state.

---

## 5. Narrative Quality

### 5.1 Fallback message leakage
**Type:** System routing issue  
**Turns:** T9, T13  
Output fallback `*That action didn't resolve as expected...` appears in narration. This is a system routing issue, not a prompt problem. The system should strip fallback messages before LLM output.

### 5.2 Generic stakes template
**Type:** Bad prompt — static template  
**Turns:** T1, T3, T5  
Stakes template sometimes generic. Replace with dynamic stakes generation based on `check.difficulty` and `intent_verb`.

### 5.3 Condition narrative callback weak
**Type:** Design — condition integration  
`bruised_ribs` referenced in T1 narration but has minimal narrative footprint after. At T8 the player tackles someone physically — a reasonable expectation of a bruised_ribs callback (increased difficulty, mention of pain) but no evidence this occurred.

### 5.4 Narration drift: Halden credits not in state
**Type:** Narration drift  
**Turns:** T3  
Halden's split payment of 100 credits is described in narration. If `inventory_add[credits, 100]` was not emitted, the fiction and state disagree — the player accepted a pouch but has zero credits.

---

## 6. Scoring Summary

| Metric | REPORT.md | REPORT-claude.md | Notes |
|--------|-----------|------------------|-------|
| Mechanical | 3/5 | 2/5 | Claude more critical on momentum observability |
| Narrative | 4/5 | 3/5 | Claude caught fail-band tone mismatches |
| System Cohesion | 3/5 | 2/5 | Both agree on ghost NPCs and quest collisions |
| Prompt Quality | 4/5 | 2/5 | Claude more critical on cross-prompt redundancy |
| Compaction | 2/5 | 2/5 | Both agree sanitization is absent |
| State Fidelity | 69% | 62% | Both agree on extraction drifts |
| Prompt Adherence | 92% | 72% | Claude weighted severity more heavily |
