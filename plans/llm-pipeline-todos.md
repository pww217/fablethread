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
- [x] Add `_failed` as second key in schema (precondition failures — populated by Plan C)
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
- [x] Log `_failed` in Python engine; pass to next narration turn as `last_turn_failed`

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

---

## G — Split Extraction Into Three Streams
*New prompt files + engine refactor. Improves per-domain accuracy. Allows streams to be skipped on simple turns.*
[→ Plan G](./extraction-stream-split.md)

- [ ] Create `extract_scene_system.j2`
- [ ] Create `extract_scene_user.j2`
- [ ] Create `extract_state_system.j2`
- [ ] Create `extract_state_user.j2`
- [ ] Create `extract_progress_system.j2`
- [ ] Create `extract_progress_user.j2`
- [ ] Add `build_scene_context()`, `build_state_context()`, `build_progress_context()` to engine
- [ ] Add `run_extraction()` to engine with stream skip logic
- [ ] Register `extract_scene`, `extract_state`, `extract_progress` in `llm_call` dispatch
- [ ] Add `USE_SPLIT_EXTRACTION` feature flag
- [ ] Log all three stream outputs under `turn_event["extraction"]` in events.jsonl
- [ ] Add condition TTL stamping on `pc_condition_add`
- [ ] Add condition TTL check at turn start with engine auto-expiry
- [ ] Add `engine_expired_conditions` injection to `extract_state_user.j2`

---

## H — Turn Inspector Debug UI
*New FastAPI server + single-page UI. Feature-flagged. Read-only view of events.jsonl.*
[→ Plan H](./debug-ui.md)

- [ ] Add `debug` block to turn event logging in engine (rendered prompts, raw outputs, state snapshots, token counts, latency)
- [ ] Capture `tokens_in`, `tokens_out`, `latency_ms` in each `llm_call` invocation
- [ ] Add `state_snapshot()` helper to engine
- [ ] Create `ccya/debug_server.py`
- [ ] Create `ccya/debug_ui.html` with three-column layout
- [ ] Add `DEBUG_UI` feature flag to engine startup
- [ ] Add `DEBUG_UI=false` and `DEBUG_UI_PORT=8765` to `.env.example`
- [ ] Verify `.env` is in `.gitignore`
- [ ] Test: start debug server, play 3 turns, confirm turns appear in UI
- [ ] Test: click a pipeline stage, confirm full rendered prompt is visible
- [ ] Test: state diff shows correct additions/removals for a known turn
