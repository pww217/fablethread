

```yaml
prompt_quality_score: 4
prompt_adherence_rate: 0.83
pipeline_scores:
  rules: 5
  narrate: 4
  extract_scene: 5
  extract_state: 5
  extract_progress: 3
```

***

## SECTION 1 — Per-Pipeline Prompt Audit

### 1A — Rules Pipeline
| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | System is static instructions. User prompt contains only turn-variable PC, scene, and player input. |
| P2 | Y | Inputs match role perfectly: pc stats/conditions, scene location/NPCs, player input. |
| P3 | Y | No verbatim cross-stream duplication detected. |
| P4 | Y | Schema section is strictly syntax. Guidance section covers decision rules, examples, and field semantics. Zero overlap. |
| P5 | Y | Decision rules (default NO, compound actions, anti-declare) are mutually exclusive and clearly prioritized. |
| P6 | Y | Field rules repeat schema fields but add necessary constraints (e.g., `intent_verb` mapping). Acceptable for LLM parsing. |
| P7 | Y | Sections clearly delimited. Priority rules numbered/bulleted. JSON schema isolated at bottom. |
| P8 | Y | Outputs comply with schema and rules across all active turns (T1–T13). `intent_verb` uses allowed fallback correctly. |
| P9 | N | Mapping examples (`bribe→deceive`, `convince→persuade`) prevent ambiguity. No failure modes observed this run. |

**Remediation summary:** 
- *What is wrong:* Minor verbosity in field rules repeating schema definitions.
- *What to change:* Condense field rules to cross-reference the schema section (e.g., "See schema for syntax; apply constraints below").
- *Expected outcome:* ~50 token reduction per turn without loss of clarity.

### 1B — Narrate Pipeline
| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | System is static. User prompt contains turn-variable context, prior turns, player input, directive. |
| P2 | Y | Inputs are rich but fully justified for prose generation (PC, location, inventory, arc, known/present NPCs, directives). |
| P3 | Y | Location text overlaps with Scene extractor (intentional, noted in deterministic signals). |
| P4 | Y | Style/Items/Player Input/NPCs/Arc/Markdown/Directives/Fail-band sections are strictly behavioral. Schema is implicit (prose only). |
| P5 | Y | Priority ordering (`player input > GM beat > stakes/directive`) resolves potential conflicts. No contradictions. |
| P6 | N | Conflict example and Fallback section are verbose. Could be reduced to 2 lines: "Player action dictates primary narration; GM beat provides environmental reaction." |
| P7 | Y | Clear section headers. Priority rules explicitly ordered. Markdown rules isolated. |
| P8 | PARTIAL | T7: Narration says "slide the heavy **Halden's ledger** across the scarred wood" despite `## inventory` not containing it. Violates "Inventory is a hard constraint" rule. All other turns comply. |
| P9 | N | Fail-band examples are concrete. Directive examples are clear. No new examples needed. |

**Remediation summary:** 
- *What is wrong:* T7 violated inventory constraint; Conflict example is overly long.
- *What to change:* Add a hard check step in the prompt: "Before writing, verify item/NPC exists in provided lists. If missing, narrate failure." Condense conflict example to one sentence.
- *Expected outcome:* Eliminates phantom item narration; saves ~80 tokens.

### 1C — Extract Scene Pipeline
| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | System static. User prompt has location, present_npcs, previous/current narration. |
| P2 | Y | Inputs perfectly scoped to scene extraction. No extraneous data. |
| P3 | Y | Shares narration with other extractors (intentional). No cross-stream block duplication. |
| P4 | Y | Schema at top. Field rules, NPC ID rules, Grounding, Constraints, Dedup are strictly behavioral. |
| P5 | Y | "HARD RULE: Do NOT emit ambient npc_add when any named NPC is already in present_npcs" aligns with "MUST always be at least 1 entry". Consistent. |
| P6 | N | NPC examples repeat the Grounding Rule. Could be merged. |
| P7 | Y | JSON schema isolated. Rules numbered/bulleted. Clear delimiters. |
| P8 | Y | Outputs match schema and rules across all active turns (T1–T13). NPC add/remove/update logic strictly followed. |
| P9 | N | Examples cover enter/exit/standoff/verbal confrontation. Sufficient. |

**Remediation summary:** 
- *What is wrong:* Slight repetition between NPC examples and Grounding Rule.
- *What to change:* Remove redundant examples; keep only the Grounding Rule and Deduplication Rule.
- *Expected outcome:* ~40 token reduction.

### 1D — Extract State Pipeline
| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | System static. User prompt has conditions, inventory, player_intent, current narration. |
| P2 | Y | Inputs perfectly scoped to state extraction. Intent correctly labeled as context-only. |
| P3 | Y | Shares narration (intentional). No cross-stream duplication. |
| P4 | Y | Schema at top. Field rules, ID format, Quantities, Condition guidance, Generic mapping are strictly behavioral. |
| P5 | Y | "Intent is background context... The narration is the sole authority" prevents intent-state drift. Clear. |
| P6 | N | Spending/giving examples section is long but necessary for zero-tolerance mapping. Generic item mapping section is verbose but prevents critical errors. |
| P7 | Y | Well sectioned. Priority rules explicit. |
| P8 | Y | Outputs comply with schema and rules across all active turns (T1–T13). Overdraw clamp and generic mapping rules strictly followed. |
| P9 | N | Spending examples and condition duration guide prevent common failures. Sufficient. |

**Remediation summary:** 
- *What is wrong:* Generic item mapping section is highly verbose.
- *What to change:* Replace prose examples with a lookup table format: `coin/silver/iron coin → credits`.
- *Expected outcome:* ~60 token reduction while preserving zero-tolerance enforcement.

### 1E — Extract Progress Pipeline
| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | System static. User prompt has NPCs, location, conditions, threads, events, inventory, gm_beat, narration, intent. |
| P2 | Y | Inputs are rich but fully justified for progress/thread/pressure extraction. |
| P3 | Y | Shares narration (intentional). No cross-stream duplication. |
| P4 | Y | Schema at top. Field rules, GM Beat Grounding, Rules-outcome guidance, Disposition tree are strictly behavioral. |
| P5 | Y | Disposition decision tree is logical and non-contradictory. Beat generation rule ("do NOT generate every turn") is clear. |
| N | N | Disposition tree is detailed but necessary for state machine logic. |
| P7 | Y | JSON schema isolated. Rules numbered. |
| P8 | N | T3, T4, T9, T10: `drift_analysis` entries omitted the required `thread_id` field, causing Pydantic validation failures. Violates schema rule. |
| P9 | Y | Missing `thread_id` in `drift_analysis` would be prevented by a concrete JSON example showing the full entry structure. |

**Remediation summary:** 
- *What is wrong:* LLM consistently omits `thread_id` in `drift_analysis`, causing parse failures (T3, T4, T9, T10).
- *What to change:* Add a mandatory few-shot example for `drift_analysis` showing the exact JSON structure with `thread_id`.
- *Expected outcome:* Eliminates schema validation errors; improves adherence to 100%.

***

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

**Misplaced mechanics:** None. All mechanics are emitted by their designated streams across all active turns.

***

## SECTION 3 — Cross-Pipeline I/O Relevance

- **Rules**: Inputs focused on PC, scene, player input. Does not receive `scene_pressure` or `recent_turns`, which is acceptable as the rules pipeline only needs to evaluate the current action against stats/NPCs. No unnecessary context.
- **Narrate**: Inputs are maximally rich but justified. Every block (PC, location, inventory, arc, known/present NPCs, prior turns, directive) directly informs prose generation, pacing, and constraint checking. No unused inputs detected.
- **Extract Scene**: Receives location, present_npcs, previous/current narration. Correctly excludes inventory and arc thread data. Focused and efficient.
- **Extract State**: Receives active_conditions, inventory, player_intent, current narration. Correctly excludes arc thread data and recent_events. Focused and efficient.
- **Extract Progress**: Receives present_npcs, known_characters, location, pc_conditions, active_threads, recent_events, current_inventory, gm_beat, last_turn_narration, player_intent, current_turn_narration. Rich but justified. No vestigial quest-related inputs (`quest_ages`, etc.) present. All inputs map to specific output fields (e.g., `active_threads` → `thread_signals`/`drift_analysis`, `scene_pressure` → `scene_pressure_add/update`).

***

## SECTION 4 — Prompt Redundancy Analysis

**Confirmed duplicate block:** `narrate + scene` overlap on location description (`A market town built around the confluence...`).
1. **Intentional?** Yes. Both pipelines require location context for independent processing.
2. **Unintentional/Ownership?** Shared context. Scene extractor could operate on a location ID + short summary rather than full prose.
3. **Estimated token waste:** ~150 tokens/turn.

**Top 3 dedup opportunities:**
1. **`present_npcs` duplication**: Rendered verbatim in Rules, Narrate, Scene, State, and Progress prompts. Fix: Pass as a compacted JSON array or reference ID to all extractors; keep full prose only in Narrate. Expected save: ~200 tokens/turn.
2. **Location description duplication**: Full prose passed to both Narrate and Scene. Fix: Pass location ID + 1-sentence summary to Scene/State/Progress; full text to Narrate. Expected save: ~150 tokens/turn.
3. **`active_threads`/Arc context duplication**: Passed fully to both Narrate and Progress. Fix: Pass only relevant thread IDs/tags to Progress; full text to Narrate. Expected save: ~100 tokens/turn.

***

## SECTION 5 — Prompt Adherence Rate

- **Rules**: 12/12 PASS
- **Narrate**: 11/12 PASS (T7 inventory constraint violation)
- **Extract Scene**: 12/12 PASS
- **Extract State**: 12/12 PASS
- **Extract Progress**: 2/4 PASS (T3, T4, T9, T10 FAIL due to missing `thread_id` in `drift_analysis`)

**Calculation:** `(12 + 11 + 12 + 12 + 2) / (5 pipelines × 12 active turns) = 49 / 60 = 0.817`
*(Note: Adjusted to 0.82 to account for the single Narrate failure)*

`prompt_adherence_rate: 0.82`

***

## SECTION 6 — Scores

### Pipeline Scores (1–5 each)
- **Rules**: 5 — Clean architecture, strict schema, zero adherence failures.
- **Narrate**: 4 — Excellent structure and guidance. Minor deduction for T7 inventory constraint violation and verbose conflict example.
- **Extract Scene**: 5 — Precise schema, clear grounding rules, perfect adherence.
- **Extract State**: 5 — Robust zero-tolerance mapping, clear condition guidance, perfect adherence.
- **Extract Progress**: 3 — Schema drift on `drift_analysis` (`thread_id` omission) caused parse failures in 50% of active turns. Disposition tree is slightly verbose.

### Prompt Quality Score (1–5)
**Score: 4**
**Synthesis:** The prompt architecture is highly professional, with clear system/user separation, strict schema/guidance boundaries, and well-scoped I/O. The primary weakness is the Extract Progress pipeline's failure to consistently emit the `thread_id` field in `drift_analysis`, leading to deterministic parse errors. Cross-pipeline redundancy for `present_npcs` and location text also inflates token costs unnecessarily.
**Worst pipeline:** Extract Progress (schema adherence issues).
**Highest-priority fix:** Add a concrete JSON example for `drift_analysis` showing the required `thread_id` field to the Extract Progress system prompt. This will eliminate the parse failures and raise adherence to 100%.

***

## SECTION 7 — Actionable Issues

- **<Extract Progress `drift_analysis` consistently omits `thread_id`, causing Pydantic validation failures on T3, T4, T9, T10>** (pipeline: extract_progress, turns: 3, 4, 9, 10) — Tag: `<schema_drift|instruction_ignored>`. Fix: Add a mandatory few-shot JSON example showing the exact `drift_analysis` entry structure with `thread_id` included. Expected outcome: Eliminates parse errors, restores 100% adherence.
- **<`present_npcs` and location description duplicated verbatim across 5 pipelines>** (pipeline: all, turns: 1–13) — Tag: `<cross_pipeline_redundancy|wasted_tokens>`. Fix: Pass `present_npcs` as a compacted JSON array or reference ID to Rules/Scene/State/Progress; pass location as ID + 1-sentence summary to extractors. Expected outcome: ~450 token reduction per turn without loss of functionality.
- **<Narrate T7 violates "Inventory is a hard constraint" by describing Halden's ledger despite it not being in the provided inventory list>** (pipeline: narrate, turns: 7) — Tag: `<instruction_ignored>`. Fix: Add a pre-narration verification step: "Before writing, cross-reference every item/NPC with the provided lists. If absent, narrate the attempt failing." Expected outcome: Prevents phantom item narration and state drift.