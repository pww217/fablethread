# LLM Pipeline Accuracy — Checklist

Full implementation details: [llm-pipeline-accuracy.md](./llm-pipeline-accuracy.md)

---

## A — Context Block Labeling
*Template changes only. Zero latency impact. Fixes narration continuity and stale-fact extraction.*
[→ Plan A](./llm-pipeline-accuracy.md#plan-a-context-block-labeling)

- [ ] Add `## PRIOR HISTORY` / `## END PRIOR HISTORY` wrapper to `_chronicle.j2`
- [ ] Add `## RECENT TURNS` / `## END RECENT TURNS` header to `_recent.j2`
- [ ] Add `## CURRENT TURN NARRATION` label in `extract_user.j2` around narration input

---

## B — Reasoning Field in Extractor
*Schema change + 2-line Python strip. ~30–60 extra output tokens. Fixes quest/inventory misclassification.*
[→ Plan B](./llm-pipeline-accuracy.md#plan-b-reasoning-field-in-extractor-schema)

- [x] Add `_reasoning` as first key in `extract_system.j2` output schema with field guidance
- [x] Add `failed` as second key in schema (precondition failures — populated by Plan C)
- [x] Verify `actions` is last key in schema definition order (removed — moved to narrate call)
- [x] Strip `_reasoning` in Python engine before applying delta

---

## C — Scope Boundaries via Rules Call
*Extends existing rules call output. Fixes spurious cross-domain extractions and silent precondition failures.*
[→ Plan C](./llm-pipeline-accuracy.md#plan-c-scope-boundaries-via-rules-call-enhancement)

- [x] Add `scope` object to `rules_system.j2` output schema (active_domains, skip_domains, implicit_preconditions, ambiguities)
- [x] Add domain-mapping guidance to `rules_system.j2` (action type → domain list)
- [x] Inject scope block at top of `extract_user.j2` from `rules_outcome.scope`
- [x] Add SKIP DOMAINS enforcement instruction to `extract_system.j2`
- [x] Log `failed` in Python engine; pass to next narration turn as `last_turn_failed`

---

## D — Active-Domain State Slicing (extractor only)
*Python engine change. Depends on Plan C. Reduces extractor input tokens on simple turns.*
[→ Plan D](./llm-pipeline-accuracy.md#plan-d-active-domain-state-slicing-extractor-only)

- [x] Build `build_state_slice()` helper in Python engine
- [x] Pass sliced state into `extract_user.j2` instead of full state
- [x] Keep full state in `narrate_system.j2` (narrator always needs full context)

---

## E — `actions` Generation Placement
*Abandoned — actions stay in extractor. Narrator outputs prose only; extractor outputs structured data.*
[→ Plan E](./llm-pipeline-accuracy.md#plan-e-actions-generation-placement)

- [x] Remove ACTIONS_JSON marker from narrate call
- [x] Restore actions to extract_system.j2 schema with guidance to draw from current narration only
- [x] Add actions field to ExtractResult model

---

## F — Compaction Redesign
*New prompt files + Python logic. Fixes fixed-cadence compaction.*
[→ Plan F](./llm-pipeline-accuracy.md#plan-f-context-compaction-redesign)

- [ ] Replace fixed turn-count trigger with token-threshold check in Python engine
- [ ] Create `ccya/prompts/compact_system.j2` (preserve/discard rules + output schema)
- [ ] Create `ccya/prompts/compact_user.j2` (inventory + established_facts + recent turns input)
- [ ] Update Python engine: archive recent_turns to chronicle, clear recent_turns, merge new_facts
- [ ] Ensure `_chronicle.j2` renders chronicle entries with `PRIOR HISTORY` label (Plan A)
