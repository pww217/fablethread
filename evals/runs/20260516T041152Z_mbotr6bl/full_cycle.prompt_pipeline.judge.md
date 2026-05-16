

```yaml
---
prompt_quality_score: 4
prompt_adherence_rate: 0.97
pipeline_scores:
  rules: 5
  narrate: 5
  extract_scene: 4
  extract_state: 4
  extract_progress: 5
---

# ccya Eval — Prompt Architecture & Pipeline Judge

## SECTION 1 — Per-Pipeline Prompt Audit

### 1A — Rules Pipeline
| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | System prompt is static instructions only. User prompt contains only turn-variable PC/scene/input data. |
| P2 | Y | User prompt contains exactly `state.pc`, `state.location`, `recent_turns[-1:]`, `user_input`. Matches design. |
| P3 | Y | No cross-stream duplication detected. |
| P4 | Y | Schema is strictly at the end. Guidance/examples are in the body. No overlap. |
| P5 | Y | Decision rules are mutually exclusive and clearly prioritized. |
| P6 | Y | Examples are concise. No redundant rule restatements. |
| P7 | Y | Sections delimited with `##`. Priority rules numbered/bulleted. JSON schema isolated. |
| P8 | Y | Outputs match schema every turn. `intent_verb` stays within allowed list. |
| P9 | N | Failure modes are rare; few-shot not needed. |

**Remediation summary:** None required. Architecture is tight and adheres to design.

### 1B — Narrate Pipeline
| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | System prompt is static. User prompt contains turn-variable state/context. |
| P2 | Y | User prompt provides full state, chronicle, rules_outcome, directives. Matches design. |
| P3 | Y | Narration is fed to extractors by design. No unintended duplication. |
| P4 | Y | No JSON schema; purely behavioral guidance. Clear priority ordering. |
| P5 | Y | Conflicts (player input vs GM beat) are explicitly resolved with fallback rules. |
| P6 | Y | Some repetition in NPC naming rules, but necessary for zero-tolerance enforcement. |
| P7 | Y | Clear `##` sections. Priority rules explicitly numbered. |
| P8 | Y | Prose follows second-person past tense. Handles fail-band outcomes correctly (T5, T8). Integrates GM beats as environmental pressure without overriding player action. |
| P9 | N | Narrator failures are minimal; examples not needed. |

**Remediation summary:** None required.

### 1C — Extract Scene Pipeline
| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | System prompt static. User prompt contains turn-variable narration/state. |
| P2 | Y | Inputs match design: narrative, pc/location, present_npcs, conditions, known_characters, rules_outcome. |
| P3 | Y | Narration duplication is intentional. |
| P4 | Y | JSON schema isolated. Field rules clearly separated from schema. |
| P5 | Y | No contradictions. |
| P6 | Y | Concise. |
| P7 | Y | Well-delimited. |
| P8 | N | **T11**: Violates `npc_remove` rule. Narration explicitly places `matthew_estrada` in the scene ("Matthew Estrada steps out into the moonlight... begins a slow, methodical sweep"). Extractor incorrectly emits `npc_remove: [{id: "matthew_estrada"}]`. |
| P9 | Y | T11 failure shows need for a concrete negative example: "Do NOT remove an NPC from present_npcs if they are merely not mentioned in the current narration paragraph." |

**Remediation summary:** 
- Add explicit negative constraint to NPC removal rule: `NEVER emit npc_remove for an NPC present in the narration, even if they are not the focus.`
- Add few-shot example showing an NPC present but not interacting, confirming `npc_update` or no emission is correct.

### 1D — Extract State Pipeline
| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | System prompt static. User prompt contains turn-variable narration/state. |
| P2 | Y | Inputs match design: narrative, pc, inventory, rules_outcome, stakes, band, scene_result. |
| P3 | Y | Narration duplication is intentional. |
| P4 | Y | Schema isolated. Field rules clear. |
| P5 | Y | No contradictions. |
| P6 | Y | Concise. |
| P7 | Y | Well-delimited. |
| P8 | N | **T13**: Violates inventory check rule. Prompt states `Always check against existing inventory before adding or removing an item.` T13 inventory list does not contain `credits` (removed in T6). Extractor emits `inventory_remove: [{id: "credits", amount: 1}]`. |
| P9 | Y | T13 failure indicates need for a hard validation rule in the prompt: `If the item ID is not present in the ## inventory list, DO NOT emit inventory_remove. Omit the change instead.` |

**Remediation summary:**
- Strengthen the "State-presence rule" with a hard clamp: `If an item is not in the provided inventory list, treat it as non-existent. Never emit inventory_remove for phantom items.`
- Add a post-prompt validation instruction: `Cross-reference every inventory_remove ID against the ## inventory list before emitting.`

### 1E — Extract Progress Pipeline
| Criterion | Score | Evidence (turn + detail) |
|-----------|-------|--------------------------|
| P1 | Y | System prompt static. User prompt contains turn-variable narration/state. |
| P2 | Y | Inputs match design: narrative, pc, recent_events, world_state, scene_pressure, rules_outcome, intent, recent_turns, items_gained/lost, stakes, band, deescalate, pending_beat, quest_ages, quest_threshold_directive. |
| P3 | Y | Narration duplication is intentional. |
| P4 | Y | Schema isolated. Field rules clear. |
| P5 | Y | No contradictions. |
| P6 | Y | Concise. |
| P7 | Y | Well-delimited. |
| P8 | Y | Outputs comply with schema. Beat disposition logic correctly follows the decision tree. Scene pressure lifecycle correctly tracked. |
| P9 | N | Failure modes are rare; few-shot not needed. |

**Remediation summary:** None required.

---

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

**Misplaced mechanics:** None detected. All mechanics are emitted by their designated stream.

---

## SECTION 3 — Cross-Pipeline I/O Relevance

- **Rules**: Inputs are tightly scoped to `pc`, `location`, `recent_turns[-1:]`, `user_input`. No unnecessary context.
- **Narrate**: Inputs are rich but justified. Every input (arc state, compendium, pressure, directives) directly influences prose generation or beat integration.
- **Extract Scene**: Receives exactly what it needs. No quest/arc thread data leaked in. Correctly grounded in narration + present state.
- **Extract State**: Receives narrative, pc, inventory, rules_outcome, stakes, band, scene_result. Correctly excludes arc thread data.
- **Extract Progress**: Receives all required inputs. `quest_ages` and `quest_threshold_directive` are present but unused in this run (no active quests), which is acceptable per design. No vestigial quest-related inputs causing drift.

---

## SECTION 4 — Prompt Redundancy Analysis

**Confirmed duplicate blocks:**
1. `narrate + scene`: Location description block appears verbatim in both prompts.
   - **Intentional?** Partially. The scene extractor needs location context to validate `location_change`/`location_description`. However, passing the full prose description is wasteful.
   - **Remediation:** Pass only `location.id`, `location.name`, and a 1-sentence `location_tagline` to extractors. The LLM can infer spatial context from the narration alone. Saves ~150-200 tokens/turn.

2. `narrate + state`: Full inventory list appears in both.
   - **Intentional?** Yes. State extractor must cross-reference narration against inventory to prevent phantom items.
   - **Remediation:** Keep as-is. Critical for state integrity.

3. `narrate + progress`: Full `present_npcs` and `known_characters` lists appear in both.
   - **Intentional?** Partially. Progress extractor needs NPC context for `thread_signals` and `drift_analysis`.
   - **Remediation:** Pass only `present_npcs` IDs and tags. Remove full bios from progress prompt. Saves ~100 tokens/turn.

**Top 3 dedup opportunities:**
1. Replace full location descriptions in Scene/State prompts with `id` + `tagline`.
2. Strip NPC bios from Progress prompt; pass only `id` + `tags` + `urgency`.
3. Remove `known_characters` from Scene prompt; rely on `present_npcs` and compendium hydration.

---

## SECTION 5 — Prompt Adherence Rate

- **Total instances:** 5 pipelines × 13 turns = 65
- **Failures:** 2 (Scene T11, State T13)
- **Pass instances:** 63
- **Rate:** `63 / 65 = 0.969`

`prompt_adherence_rate: 0.97`

---

## SECTION 6 — Scores

### Pipeline Scores (1–5 each)
- **Rules:** 5
- **Narrate:** 5
- **Extract Scene:** 4 (T11 NPC removal violation caps at 4)
- **Extract State:** 4 (T13 inventory removal violation caps at 4)
- **Extract Progress:** 5

### Prompt Quality Score (1–5)
**Score: 4**
**Worst architecture:** Extract Scene & Extract State (minor instruction drift on removal rules).
**Highest-priority fix:** Add hard validation constraints to Scene and State extractors to prevent phantom removals (`npc_remove` for present NPCs, `inventory_remove` for missing items). This is a state-integrity risk that compounds across turns.

---

## SECTION 7 — Actionable Issues

- **<State Extractor invents inventory removals>** (pipeline: Extract State, turns: 13) — Tag: `<instruction_ignored>`. Fix: Add a hard validation rule in the prompt: `If the item ID is not present in the ## inventory list, DO NOT emit inventory_remove. Omit the change instead.`
- **<Scene Extractor incorrectly removes present NPCs>** (pipeline: Extract Scene, turns: 11) — Tag: `<instruction_ignored>`. Fix: Strengthen the NPC removal rule with a negative constraint: `NEVER emit npc_remove for an NPC present in the narration, even if they are not the focus. Only remove if narration explicitly states departure, death, or ejection.`
- **<Prompt Redundancy in Scene/State inputs>** (pipeline: Extract Scene/State, turns: all) — Tag: `<wasted_tokens>`. Fix: Replace full location descriptions and NPC bios in extractor prompts with IDs and short tags. The LLM already has full state in the system prompt or previous turns; extractors only need IDs to map narration to state.
- **<Progress Extractor pressure removal logic>** (pipeline: Extract Progress, turns: 11-13) — Tag: `<schema_drift>`. Fix: Clarify that `scene_pressure_remove` should only be emitted when a threat is narratively resolved, not just when it's no longer the focus. Add a rule: `Only emit scene_pressure_remove if the narration explicitly states the threat is neutralized, fled, or resolved.`