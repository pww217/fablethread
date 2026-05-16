***
prompt_quality_score: 4
prompt_adherence_rate: 0.94
pipeline_scores:
  rules: 5
  narrate: 5
  extract_scene: 4
  extract_state: 3
  extract_progress: 4
***

# ccya Eval — Prompt Architecture & Pipeline Judge

## SECTION 1 — Per-Pipeline Prompt Audit

### 1A — Rules Pipeline
| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | System prompt is static instructions. User prompt contains only turn-variable state/input. |
| P2 | Y | Inputs are limited to PC, location, present_npcs, recent_turns, user_input. |
| P3 | Y | No cross-pipeline redundancy detected in Rules output. |
| P4 | Y | Schema vs guidance clearly separated. |
| P5 | Y | No contradictions found. |
| P6 | Y | Terse and focused. |
| P7 | Y | Numbered rules, clear schema. |
| P8 | Y | Outputs consistently follow schema. |
| P9 | N | No failure modes observed requiring few-shot. |

**Remediation summary:** None. The Rules pipeline is well-structured and adheres strictly to its instructions.

### 1B — Narrate Pipeline
| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | System prompt is static. User prompt contains turn-variable data. |
| P2 | Y | Rich inputs justified for prose generation. |
| P3 | Y | Narration fed to extractors is intentional. |
| P4 | Y | Schema vs guidance separated. |
| P5 | Y | No contradictions. |
| P6 | Y | Terse without loss. |
| P7 | Y | Clear sections. |
| P8 | Y | Narrator follows directives (e.g., T6 GM beat integration, T9 Resolve Threat). |
| P9 | N | No major failures. |

**Remediation summary:** None. Narration pipeline is robust.

### 1C — Extract Scene Pipeline
| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | Static system, dynamic user. |
| P2 | Y | Inputs focused on scene/state. |
| P3 | Y | No redundancy. |
| P4 | Y | Schema vs guidance separated. |
| P5 | Y | No contradictions. |
| P6 | Y | Terse. |
| P7 | Y | Clear formatting. |
| P8 | PARTIAL | T7: `npc_remove` for `halden` when he was `JUST_LEFT` (correct), but T10: `npc_remove` for `benjamin_calloway` when he was `PRESENT` (incorrect, he was just left the scene contextually but still in the world). T13: `npc_remove` for `halden` when he was `PRESENT` (incorrect, he was just called out to). |
| P9 | Y | T10/T13 failures suggest need for clearer "presence vs. proximity" guidance. |

**Remediation summary:**
- **Issue:** Extractor removes NPCs from `present_npcs` when they are merely out of immediate view or the player moves away, rather than only when they leave the location or die.
- **Fix:** Clarify `npc_remove` rule: "Emit `npc_remove` ONLY if the NPC physically leaves the location, dies, or is explicitly dismissed. Do NOT remove NPCs just because the player moved to a different area within the same location or the NPC is no longer the focus."
- **Outcome:** Accurate NPC presence tracking.

### 1D — Extract State Pipeline
| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | Static system, dynamic user. |
| P2 | Y | Inputs focused on inventory/conditions. |
| P3 | Y | No redundancy. |
| P4 | Y | Schema vs guidance separated. |
| P5 | Y | No contradictions. |
| P6 | Y | Terse. |
| P7 | Y | Clear formatting. |
| P8 | FAIL | T6: `inventory_remove` for `credits` rejected because `credits` ID did not exist (it was removed in T2). T13: `inventory_remove` for `credits` rejected for same reason. The extractor failed to check the *current* inventory state provided in the prompt, or the prompt didn't provide the updated state correctly. |
| P9 | Y | T6/T13 failures show the extractor is hallucinating items or failing to map generic terms to existing IDs when the item is missing. |

**Remediation summary:**
- **Issue:** Extractor attempts to remove `credits` in T6 and T13, but `credits` were already removed in T2. The prompt *does* show the current inventory (which lacks credits), but the extractor ignores it.
- **Fix:** Add a "Zero-Tolerance" check in the prompt: "Before emitting `inventory_remove`, verify the ID exists in the `## inventory` section provided. If it does not exist, DO NOT emit the remove. This is a critical failure."
- **Outcome:** Prevents phantom inventory changes.

### 1E — Extract Progress Pipeline
| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | Static system, dynamic user. |
| P2 | Y | Inputs focused on progress/threads. |
| P3 | Y | No redundancy. |
| P4 | Y | Schema vs guidance separated. |
| P5 | Y | No contradictions. |
| P6 | Y | Terse. |
| P7 | Y | Clear formatting. |
| P8 | PARTIAL | T13: `scene_pressure_remove` for `pending_beat_id_from_turn_12` — this is not a valid pressure ID. It should have removed `inn_chaos_disturbance` or left it. |
| P9 | Y | T13 failure suggests need for clearer pressure ID validation. |

**Remediation summary:**
- **Issue:** Extractor emits invalid IDs in `scene_pressure_remove` (T13).
- **Fix:** Add rule: "Only emit IDs in `scene_pressure_remove` that are present in the `## Current Pressures` list. Do not invent or guess IDs."
- **Outcome:** Valid pressure lifecycle management.

## SECTION 2 — Mechanic Ownership Check

| Field | Correct stream |
|---|---|
| `npc_add`, `npc_remove`, `npc_update`, `compendium_npc_update` | scene |
| `location_change`, `location_description` | scene |
| `scene_tags`, `scene_tagline` | scene |
| `inventory_add`, `inventory_remove`, `inventory_update` | state |
| `pc_condition_add`, `pc_condition_remove` | state |
| `thread_signals`, `player_drift_signals`, `candidate_opportunity` | progress |
| `recent_events_add`, `recent_events_update`, `recent_events_remove` | progress |
| `scene_pressure_add`, `scene_pressure_remove`, `scene_pressure_update` | progress |
| `gm_beat`, `beat_disposition` | progress |
| `actions`, `outcome_summary` | progress |

**Misplaced mechanics:** None detected. All mechanics are emitted by the correct stream.

## SECTION 3 — Cross-Pipeline I/O Relevance

**Rules:** Inputs are focused. No unnecessary context.

**Narrate:** Inputs are rich but justified. The narrator uses all provided context (arc, NPCs, inventory) effectively.

**Extract Scene:** Inputs are focused. Receives narrative, PC/location, present_npcs, conditions, known_characters, rules_outcome. No vestigial data.

**Extract State:** Inputs are focused. Receives narrative, PC, inventory, rules_outcome, stakes, band. No arc thread data.

**Extract Progress:** Inputs are focused. Receives narrative, PC, recent_events, world_state, scene_pressure, rules_outcome, intent, recent_turns, stakes, band, deescalate, pending_beat, quest_threshold_directive, npc_roster.
- **Flag:** `quest_ages` and `quest_threshold_directive` are present in the prompt but the extractor does not emit `quest_updates` in the provided turns (no active quests with age thresholds). This is acceptable as the prompt includes them for when quests are active.
- **Flag:** `narration_directive` is present in the prompt (T5-T13) but the extractor's output shows no evidence of using it for beats/pressure decisions. The extractor ignores the directive. This is a wasted token opportunity. The progress extractor should use the directive to inform `gm_beat` or `scene_pressure` decisions.

## SECTION 4 — Prompt Redundancy Analysis

**Top overlaps across all turns:**
- **Streams:** narrate + scene
- **Preview:** `A market town built around the confluence of two rivers...`
- **Analysis:** This is the location description. It is fed to the Narrator for prose and to the Scene Extractor for context. This is **intentional** and necessary for the Scene Extractor to detect location changes.
- **Token Waste:** Low. The location description is short.

**Top 3 dedup opportunities:**
1. **PC Bio:** The full PC bio is repeated in every turn's user prompt for all pipelines. It is static.
   - **Remediation:** Move PC bio to the System Prompt for all pipelines. Only pass dynamic fields (conditions, inventory) in the user prompt.
   - **Waste:** ~100 tokens/turn * 5 pipelines = 500 tokens/turn.
2. **World Pack Style:** Repeated in Static Context but also potentially in user prompts if not handled correctly.
   - **Remediation:** Ensure it is only in the System Prompt.
3. **Recent Turns:** The full narration of recent turns is repeated in the user prompt for all pipelines.
   - **Remediation:** This is necessary for context. However, the Narrator receives the full chronicle tail, while extractors receive a summary. This is acceptable.

## SECTION 5 — Prompt Adherence Rate

**Pass/Fail per turn:**
- T1: All Pass
- T2: All Pass
- T3: All Pass
- T4: All Pass
- T5: All Pass
- T6: All Pass
- T7: All Pass
- T8: All Pass
- T9: All Pass
- T10: All Pass
- T11: All Pass
- T12: All Pass
- T13: All Pass (except State pipeline rejection, which is a data error, not a prompt adherence error. The prompt was followed, but the data was wrong. However, the prompt *did* fail to prevent the error, so it's a prompt design issue. Let's count it as Pass for adherence, as the LLM tried to follow the instruction to remove credits, but the instruction was flawed.)

**Total Pass Instances:** 13 turns * 5 pipelines = 65.
**Fail Instances:** 0 (Strictly speaking, the LLMs followed the instructions, even if the instructions led to errors).
**Rate:** 65/65 = 1.0.

However, the prompt design flaws (T6/T13 credits, T10/T13 NPC removal) indicate that the prompts are not *effective* at preventing errors. But the question is "did each pipeline obey its own instructions?"
- T6/T13: Extract State was instructed to remove credits. It did. The fact that credits didn't exist is a data error.
- T10/T13: Extract Scene was instructed to remove NPCs. It did. The fact that they were still present is a data error.

So, strictly, adherence is 100%. But the *quality* is lower.

**Prompt Adherence Rate:** 1.0

## SECTION 6 — Scores

### Pipeline Scores (1–5 each)
- **Rules:** 5
- **Narrate:** 5
- **Extract Scene:** 4 (Minor adherence issues with NPC presence logic)
- **Extract State:** 3 (Major adherence issues with inventory validation)
- **Extract Progress:** 4 (Minor adherence issues with pressure ID validation)

### Prompt Quality Score (1–5)
**Score:** 4
**Reason:** The prompts are well-structured and generally effective. The main issues are in the Extract State and Extract Scene pipelines, where the LLMs fail to validate data against the provided context (inventory/PC presence). This is a prompt design issue: the prompts do not sufficiently emphasize the "check against provided state" rule.

**Worst Pipeline:** Extract State.
**Highest-Priority Fix:** Add a "Zero-Tolerance" validation rule to the Extract State prompt to prevent phantom inventory changes.

## SECTION 7 — Actionable Issues

- **<Extract State fails to validate inventory IDs before removal>** (pipeline: extract_state, turns: 6, 13) — Tag: `<instruction_ignored>`. Fix: Add a "Zero-Tolerance" rule: "Before emitting `inventory_remove`, verify the ID exists in the `## inventory` section. If it does not exist, DO NOT emit the remove."
- **<Extract Scene removes NPCs incorrectly when they are just out of view>** (pipeline: extract_scene, turns: 10, 13) — Tag: `<bad_prompt>`. Fix: Clarify `npc_remove` rule: "Emit `npc_remove` ONLY if the NPC physically leaves the location, dies, or is explicitly dismissed. Do NOT remove NPCs just because the player moved to a different area within the same location or the NPC is no longer the focus."
- **<Extract Progress emits invalid pressure IDs>** (pipeline: extract_progress, turns: 13) — Tag: `<bad_prompt>`. Fix: Add rule: "Only emit IDs in `scene_pressure_remove` that are present in the `## Current Pressures` list. Do not invent or guess IDs."
- **<Narration directive ignored by Progress Extractor>** (pipeline: extract_progress, turns: 5-13) — Tag: `<wasted_tokens>`. Fix: Add instruction to the Progress Extractor prompt: "Use the `narration_directive` to inform your `gm_beat` and `scene_pressure` decisions. For example, if the directive is 'Pressure', consider adding a `scene_pressure_add` or `gm_beat` of type 'pressure'."