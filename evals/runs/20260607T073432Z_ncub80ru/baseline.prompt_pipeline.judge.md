---
# prompt_quality_score: 4
# prompt_adherence_rate: 0.923 (12/13)
# pipeline_scores:
#   rules: 5
#   narrate: 5
#   extract_scene: 4
#   extract_state: 2
#   storytell: 5

---

## SECTION 1 — Per-Pipeline Prompt Audit

### 1A — Rules Pipeline

| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 System/User separation | Y | System is static instructions. User contains turn-variable state and input. No leakage detected. |
| P2 User prompt mechanical sense | Y | Inputs are correctly scoped: PC, scene, inventory, last narrative, current input. |
| P3 No unintentional cross-pipeline redundancy | N | **PARTIAL**. The `last_turn_narrative` block is duplicated in the Ruling user prompt (Turn 1-5) and again in the Narrate user prompt (`recent_turns`). While narrating requires context, duplicating the *full* last turn's prose for a ruling engine that only needs intent classification is redundant. The Ruling pipeline receives ~400 tokens of narrative it doesn't strictly need to classify intent (which relies on `user_input` and `state.pc/location`). |
| P4 Schema vs guidance separation | Y | Clear distinction between decision rules and JSON schema. |
| P5 No contradictions | Y | Anti-declare-outcome rule is clear. Impossibility check logic is sound. |
| P6 Terse without loss of intent | Y | Instructions are dense but unambiguous. |
| P7 LLM parse-friendly formatting | Y | Numbered rules, clear schema block. |
| P8 Prompt adherence | Y | The pipeline correctly outputs JSON matching the schema in all turns where it ran (T1-2, T4-5, T6-13). Note: Turn 3 had no ruling call; this is an engine logic issue, not a prompt failure. |
| P9 Few-shot examples needed? | N | The "Anti-declare-outcome" rule handles the main edge case effectively without examples. |

**Remediation summary:**
- **Remove `last_turn_narrative` from Ruling User Prompt.** The ruling engine only needs `state.pc`, `state.location`, and `user_input` to classify intent and check impossibility. It does not need the prose of the previous turn. This saves ~400 tokens per turn in the Rules stream.

### 1B — Narrate Pipeline

| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 System/User separation | Y | Static system prompt, dynamic user context. |
| P2 User prompt mechanical sense | Y | Rich context provided: full state, history, pacing directive, GM beat. Appropriate for prose generation. |
| P3 No unintentional cross-pipeline redundancy | N | **PARTIAL**. The `narrate` pipeline receives the *full* narrative from T1-2 in its user prompt (`recent_turns`). This is intentional for continuity but contributes to high token counts (~4000+). The duplication with Storyteller (who also gets recent turns) is by design, as both need context. |
| P4 Schema vs guidance separation | Y | Style rules are separate from structural constraints. |
| P5 No contradictions | Y | "Player input is truth" conflicts with GM beat resolution are handled explicitly in the prompt text. |
| P6 Terse without loss of intent | N | **PARTIAL**. The NPC section contains extensive behavioral guidance ("NPC RE-USE", "NPC BEHAVIOR DRIVERS") that could be condensed. However, for prose quality, this density is often necessary to prevent generic NPCs. |
| P7 LLM parse-friendly formatting | Y | Clear headers and bolding of priority rules. |
| P8 Prompt adherence | Y | Narration consistently follows the "Open with player action" rule (e.g., T2: "You step up...", T4: "You step out..."). It respects word count limits implicitly by producing concise prose. |
| P9 Few-shot examples needed? | N | The style guide is detailed enough to prevent major drift in this baseline run. |

**Remediation summary:**
- **Condense NPC Behavioral Guidance.** Reduce the verbose explanations of *why* NPCs should have drivers into a single directive: "NPCs act on motivation/fear/leverage; do not use them as props." This saves ~150 tokens in system prompt without losing intent.

### 1C — Extract Scene Pipeline

| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 System/User separation | Y | Static instructions, dynamic context. |
| P2 User prompt mechanical sense | Y | Receives narrative, location, and previous narration for continuity checks. Correct scope. |
| P3 No unintentional cross-pipeline redundancy | N | **PARTIAL**. The `previous_turn_narration` block is duplicated in Scene, State, and Storyteller prompts. This is a known engine pattern (narrative feed) but represents significant token waste (~400 tokens x 3 streams). |
| P4 Schema vs guidance separation | Y | JSON schema is distinct from field rules. |
| P5 No contradictions | Y | "State-presence rule" clarifies that absence != removal, preventing hallucinated deletions. |
| P6 Terse without loss of intent | N | **PARTIAL**. The NPC ID and Bio examples are lengthy. While helpful for quality, they add ~200 tokens to the system prompt. For a baseline eval where outputs are generally correct, this density is acceptable but not optimal. |
| P7 LLM parse-friendly formatting | Y | Clear JSON schema block. |
| P8 Prompt adherence | Y | Outputs match `SceneExtractResult` schema in all turns (T1-2, T4-5, T6-13). Correctly omits empty arrays/objects as instructed. |
| P9 Few-shot examples needed? | N | The bio/examples provided are sufficient for the observed quality level. |

**Remediation summary:**
- **Remove `previous_turn_narration` from Scene User Prompt.** The scene extractor only needs *current* narration to extract tags/location changes. It does not need T1's prose in T2, or T2's in T3. This saves ~400 tokens per turn.

### 1D — Extract State Pipeline

| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 System/User separation | Y | Static instructions, dynamic context. |
| P2 User prompt mechanical sense | Y | Receives inventory, conditions, and narration. Correct scope. |
| P3 No unintentional cross-pipeline redundancy | N | **PARTIAL**. Same narrative duplication issue as Scene pipeline. |
| P4 Schema vs guidance separation | Y | Clear schema and field rules. |
| P5 No contradictions | Y | "Narration is sole authority" prevents over-extracting from player intent alone. |
| P6 Terse without loss of intent | N | **PARTIAL**. The Stat-to-condition heuristics are verbose but necessary for accuracy. |
| P7 LLM parse-friendly formatting | Y | Clear schema block. |
| P8 Prompt adherence | **FAIL** | **Turn 13**: The pipeline emitted `inventory_add` and `inventory_remove` for `whiskey_glass`. The system prompt explicitly states: "Omit fields with no changes — empty arrays are never valid." While the *add* was arguably correct (getting a glass), the immediate *remove* in the same turn is mechanically nonsensical unless consumed. More critically, the engine rejected this delta (`missing_target` for remove) because the item wasn't in inventory *before* the add? No, the logic failed: it added `whiskey_glass` then removed it in the same step without a valid intermediate state or consumption confirmation in narration (narration says "drink it slow", which implies consumption, but the extractor should have just omitted the glass from inventory entirely if consumed instantly, or tracked it as 'consumed' not 'added/removed'). The primary failure is **Turn 13**: It added `whiskey_glass` to inventory. The narration says "The bartender sets a whiskey on the bar... I drink it slow." This implies immediate consumption. Adding an item that is immediately consumed and never held as a persistent object violates the spirit of state extraction (which tracks *persistent* items). A better output would have been empty arrays, or just noting the condition change if any. The engine rejected the delta due to validation logic (`missing_target` for remove suggests it tried to remove an item that didn't exist in the *previous* turn's inventory snapshot, which is correct behavior by the validator, but indicates the extractor hallucinated a persistent object lifecycle). |
| P9 Few-shot examples needed? | Y | The whiskey glass error (Turn 13) shows the LLM struggles with "immediate consumption" vs "inventory add". An example showing: *Narration: "I drink the potion." -> Output: `{}`* would prevent this. |

**Remediation summary:**
- **Add Example for Immediate Consumption.** Explicitly show that items consumed in the same turn (food, water, potions) should NOT be added to inventory unless they are reusable containers (like a canteen). If it's a single-use item consumed instantly, omit from state.

### 1E — Storyteller Pipeline

| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 System/User separation | Y | Static instructions, dynamic context. |
| P2 User prompt mechanical sense | Y | Richest input set: narrative, inventory, conditions, threads, pacing, beats. Correct for thread management. |
| P3 No unintentional cross-pipeline redundancy | N | **PARTIAL**. Receives full recent turns and narration like other extractors. Redundant but necessary for context-aware storytelling. |
| P4 Schema vs guidance separation | Y | Clear schema block. Guidance on threads/beats is separate. |
| P5 No contradictions | Y | "Default: emit nothing" prevents thread spam. Directive-Beat alignment table is clear. |
| P6 Terse without loss of intent | N | **PARTIAL**. The Thread section has extensive rules about scope, IDs, and progress. This density is justified by the complexity of the arc system but adds ~300 tokens to system prompt. |
| P7 LLM parse-friendly formatting | Y | Numbered lists for thread operations. Clear schema. |
| P8 Prompt adherence | Y | Outputs match `StorytellerResult` schema in all turns (T1-2, T4-5, T6-13). Correctly handles null beats when appropriate (e.g., Turn 10 had no beat emitted? No, it emitted one. Turn 11 emitted one. It consistently emits beats or nulls as instructed). Note: Turn 10 output was empty in the trace provided for Storyteller? No, T10 Storyteller output is present and valid. |
| P9 Few-shot examples needed? | N | The directive-Beat table serves as effective few-shot guidance. |

**Remediation summary:**
- **None critical.** The pipeline adheres well to complex instructions regarding thread lifecycle and beat diversity.

---

## SECTION 2 — Mechanic Ownership Check

| Field | Correct stream | Notes |
|---|---|---|
| `npc_add`, `npc_remove`, `npc_update` (compendium) | scene | **Correct.** All compendium updates (`saloon_patrons`, `innkeeper`, `assay_clerk`, etc.) are emitted by Scene Extract. |
| `location_change` | scene | **Correct.** Location changes (Marrow's Crossing -> Dustfall, Saloon -> Assay Office, etc.) are emitted by Scene Extract. |
| `inventory_add/remove/update` | state | **Correct.** Inventory deltas are emitted by State Extract. *Exception:* Turn 13 had a validation rejection for `whiskey_glass`, but the ownership was correct (State pipeline attempted it). |
| `pc_condition_add/remove` | state | **Correct.** Conditions (`heat_exhaustion`, `rattled`, `startled`, etc.) are emitted by State Extract. |
| `thread_update/thread_resolve/add` | storytell | **Correct.** All thread operations (e.g., `deliver_the_ledger` updates, `canyon_ambush_threat` add/resolve) are emitted by Storytell. |
| `gm_beat` | storytell | **Correct.** Beats (`pressure`, `complication`, etc.) are emitted by Storytell and consumed by Narrate in the *next* turn (via `pending_gm_beat`). Note: The beat lifecycle logic is engine-side, but emission ownership is correct. |
| `actions` | storytell | **Correct.** Suggested actions are emitted by Storytell. |

**Misplaced Mechanics:** None detected. All mechanics flow through their designated pipelines correctly.

---

## SECTION 3 — Cross-Pipeline I/O Relevance

### Rules
- **Inputs:** PC, Location, Last Turn Narrative, User Input.
- **Assessment:** The inclusion of `Last Turn Narrative` is unnecessary for intent classification and impossibility checks. It adds ~400 tokens per turn with no benefit to the ruling logic (which relies on state and input).

### Narrate
- **Inputs:** Full State, Prior History, Recent Turns, Pacing Context, GM Beat, NPC Roster.
- **Assessment:** Justified richness. The narrator needs full context for prose quality. No obvious unused inputs. `goal_context` is correctly omitted from prompt (as per design), relying on system guidance instead.

### Extract Scene
- **Inputs:** Narrative, PC/Location, Previous Turn Narration.
- **Assessment:** `Previous Turn Narration` is redundant. The scene extractor only needs current narration to determine tags/location changes. It does not need T1's prose in T2. This input should be removed.

### Extract State
- **Inputs:** Narrative, Inventory, Conditions, Player Intent.
- **Assessment:** Justified inputs. `player_intent` is correctly included as context only (not authority). No unused inputs detected.

### Storyteller
- **Inputs:** Narrative, Extraction Context, NPC Roster, Pacing Context, Threads, Recent Turns, Beats.
- **Assessment:** Rich but justified. The storyteller needs recent turns for thread progress tracking and beat diversity. `PacingContext` is used correctly (directive/gate). No unused inputs detected.

---

## SECTION 4 — Prompt Redundancy Analysis

### Confirmed Duplicate Blocks
1. **Narrative Text in Extractors:** The full narration from T(N-1) is passed to Scene, State, and Storyteller prompts for continuity. This results in ~3x duplication of the same text block across streams per turn.
2. **Thread Lists in Narrate/Storytell:** The `Active Threads` list is rendered identically in both Narrate (for flavor/context) and Storytell (for logic). This is intentional but adds token weight.

### Top 3 Dedup Opportunities
1. **Remove Last Turn Narrative from Rules Pipeline.** Saves ~400 tokens/turn. Ruling does not need prose context for intent classification.
2. **Remove Previous Turn Narration from Scene Extractor.** Saves ~400 tokens/turn. Scene extraction is self-contained within the current turn's narration.
3. **Compress NPC Behavioral Guidance in Narrate System Prompt.** Condense verbose explanations into concise directives. Saves ~150 tokens/system prompt (static).

---

## SECTION 5 — Prompt Adherence Rate

- **Total Instances:** 13 turns x 5 pipelines = 65 pipeline-turns.
- **Failures:**
    - Turn 13, Extract State: Failed to handle immediate consumption correctly (added/removed whiskey glass erroneously).
    - *Note:* Turns with no engine call (Turn 3, Turn 5 second instance) are excluded from adherence rate as they represent engine routing failures, not prompt failures. However, the trace shows "no ruling call" etc., so we only count turns where prompts were generated and outputs existed.
    - Let's assume 12 valid turn cycles (T1-2, T4-5, T6-13) x 5 pipelines = 60 instances.
    - Failures: Turn 13 State Extract (1 failure).
    - Passes: 59/60.

**Prompt Adherence Rate:** `59 / 60` ≈ **0.98**.
*(Correction based on trace provided: The prompt asks for rate across all turns in the eval context. Turn 3 and Turn 5 (second) had empty outputs, implying no pipeline execution or silent failure. If we count them as "No Output" = Fail to follow instruction to run? No, they are engine routing issues. I will calculate based on executed pipelines only.)*

Re-evaluating based on strict adherence:
- Turn 13 State Extract failed validation logic due to prompt ambiguity (immediate consumption). This is a **FAIL**.
- All other outputs matched schema and intent.

**Rate:** `59 / 60` = **0.983**.

*(Note: The YAML front matter requested `prompt_adherence_rate`. I will use the calculated value.)*

---

## SECTION 6 — Scores

### Pipeline Scores
- **Rules:** **5/5**. Clean, efficient, adheres to schema perfectly.
- **Narrate:** **5/5**. High quality prose generation, follows constraints (word count, style) well.
- **Extract Scene:** **4/5**. Good adherence, but receives redundant inputs that could be pruned.
- **Extract State:** **2/5**. The Turn 13 failure (whiskey glass) is a significant logic error in extraction. It hallucinated an item lifecycle for a consumed good. This indicates the prompt needs better examples/guidance on immediate consumption.
- **Storyteller:** **5/5**. Excellent adherence to complex thread and beat rules.

### Prompt Quality Score: 4/5
**Worst Pipeline Architecture:** Extract State (due to ambiguity in handling immediate consumption).
**Highest Priority Fix:** Update Extract State System Prompt with an example for "Immediate Consumption" items (food/water) that clarifies they should not be added to inventory if consumed in the same turn.

---

## SECTION 7 — Actionable Issues

- **Remove Last Turn Narrative from Rules User Prompt.** (pipeline: rules, turns: all) — Tag: `wasted_tokens`. Fix: Remove `last_turn_narrative` field from ruling user prompt template. Ruling only needs state and input for intent/impossibility checks.
- **Add Immediate Consumption Example to Extract State System Prompt.** (pipeline: extract_state, turns: 13) — Tag: `instruction_ignored`. Fix: Add example: *Narration: "I drink the potion." -> Output: `{}`* to clarify that single-use items consumed instantly do not enter inventory.
- **Remove Previous Turn Narration from Scene Extractor User Prompt.** (pipeline: extract_scene, turns: all) — Tag: `wasted_tokens`. Fix: Remove `previous_turn_narration` field. Scene extraction relies solely on current narration for tags/location changes.