# Integration Points — Core Game Engine

Every place where two mechanics/steps/pipelines/features overlap or interact in the core engine.

Scope: Seed system, turn pipeline stages (Step 0 ruling through end), narration, extraction, application, persistence.
Excluded: Tooling/debug/eval/CLI (ev.py, tv, scripts), test files, static/frontend files.

**Total: 72 integration points across 13 categories.**

---

## Problematic Integration Points — Validation & Effort Assessment

The following integration points were flagged as most likely to cause bugs. Each has been validated against source code with a level-of-effort assessment for resolution.

### INT-031 — Compendium dedup silently redirects NPC IDs by name match

**Source:** `ccya/engine/extraction/utils.py:88-126`

**Validated:** Yes. `_dedup_compendium_update()` does case-insensitive name matching against existing NPCs. If a proposed NPC name matches an existing NPC's name, the ID is silently redirected. No warning is logged.

**Risk:** Medium. If two NPCs have the same name (e.g., "Guard" appears in both scene and state extraction), the new one gets silently merged into the old one. This is by design for dedup, but the silent redirect means data loss is invisible.

**Effort: LOW — 1 hour**

Add a debug log when a redirect happens (already partially logged at pipeline.py:226-230, but only at debug level). The redirect tracking is already captured in the extraction event (`compendium_dedup_redirects`), so checkers can detect it. No code changes needed — just ensure the log level is appropriate for production visibility.

---

### INT-072 — Cross-stream dedup on both Add and Update arrays

**Source:** `ccya/engine/extraction/pipeline.py:200-252`

**Validated:** Yes. The dedup runs separately on `compendium_npc_update` (line 216-231) and `compendium_npc_add` (line 233-252). Both dedup against the *existing* compendium, not against each other. If scene extracts "Guard" and state extracts "Guard", both get deduped to the same existing NPC ID. The dedup redirect is logged and recorded in the extraction event.

**Risk:** Low. The dedup is against existing compendium state, not cross-stream. The redirect tracking is already in the event data. No silent data loss — it's just that two streams extracting the same NPC results in one entry. This is the intended behavior.

**Effort: NONE** — Already handled correctly. The dedup redirect is logged and captured in the event.

---

### INT-071 — `_coerce_scene_json()` silently transforms malformed LLM output

**Source:** `ccya/engine/extraction/utils.py:129-175`

**Validated:** Yes. Coerces strings to dicts (lines 136-159), deletes empty `thread_add` and `arc_resolve` (lines 162-173). When the LLM returns `"bystanders"` instead of `[{"id": "bystanders"}]`, it's silently transformed. When the LLM returns `{"thread_add": []}`, it's silently deleted.

**Risk:** High. Bad coercion = wrong data in state with no trace. A string "Guard" becomes `{"id": "guard"}` — the ID is derived from the string, not validated. An empty `thread_add: []` is deleted (correct), but a malformed `thread_add: {}` without required fields is also deleted silently.

**Effort: MEDIUM — 4 hours**

Add a `"coerced"` flag to the extraction event when coercion occurs, logging what was coerced and the before/after values. Specifically:
- Log and flag when a string NPC entry is coerced to a dict
- Log and flag when an entry missing an `id` field has one derived from `name`
- Log and flag when `thread_add` or `arc_resolve` are deleted (not coerced, but silently dropped)
- This enables checkers to detect coercion rates and flag when the LLM consistently produces malformed output

---

### INT-017 — Beat single-turn commitment: ruling sets `pending_gm_beat`, narrate reads it

**Source:** `ccya/engine/ruling.py:221-227`, `ccya/engine/narrate.py:181`

**Validated:** Yes. Ruling sets `pending_gm_beat` at ruling.py:222 (or sets to `None` at ruling.py:224). Narrate reads it at narrate.py:181. The beat is never explicitly cleared — it persists in state and is overwritten by the next turn's ruling.

**Risk:** Low. The "always replace or pop" rule at ruling.py:221-224 means the beat is overwritten every turn. If ruling fails to select a beat, it sets `pending_gm_beat = None`, which is correct. The beat persists until overwritten, which is the intended behavior for same-turn consumption.

**Effort: LOW — 30 minutes**

Add an explicit `state.meta.pending_gm_beat = None` after narrate reads it, for clarity. Currently the beat "leaks" to the next turn as `None` (which is fine) but the intent isn't clear from the code. A comment clarifying the ownership model would suffice.

---

### INT-030 — Post-delta virtual state for record stream

**Source:** `ccya/engine/extraction/context.py:32-71`

**Validated:** Yes. `_build_post_delta_context()` creates a combined delta from scene_result + state_result, applies it to a state copy via `apply_delta()`, then extracts the post-delta view for the record stream.

**Risk:** Low. If scene or state extraction fails (skipped), the post-delta context simply won't have that stream's changes. The pipeline handles skipped streams gracefully (defaults to empty results). The record stream always runs even if scene/state fail.

**Effort: NONE** — Already handled correctly. Skipped streams produce empty results, which means the post-delta context reflects only the successful streams. This is the correct behavior.

---

### INT-047 — Two-step world state promotion: record sets `world_state_candidate`, sanitizer promotes

**Source:** `ccya/engine/turn_state.py:345-352`, `ccya/engine/thread_sanitizer.py:479-485`

**Validated:** Yes. Record sets `world_state_candidates` in `turn_state.py:345-352` when a thread resolves with `world_state_candidate`. The sanitizer reads these at `thread_sanitizer.py:150-152` (TTL-filtered) and does an atomic swap at `thread_sanitizer.py:482-485`.

**Risk:** Medium. If sanitizer is disabled (`sanitize_every=0`), world state never gets promoted. Candidates accumulate until TTL expiry (at `sanitize_every * 2` turns, which is 0 when sanitizer is disabled — so candidates are immediately purged). This means world state candidates are lost entirely when sanitizer is disabled.

**Effort: LOW — 2 hours**

Add a config warning when `sanitize_every=0` and `state.world_state_candidates` is non-empty. Alternatively, add a fallback path in `apply_delta()` that promotes candidates when the sanitizer won't run. The simplest fix: in `apply_delta()`, check for non-empty `world_state_candidates` and promote them if sanitizer is disabled.

---

### INT-040 — Auto-dormant + urgency decay runs every turn before record updates

**Source:** `ccya/engine/turn_state.py:550-562`

**Validated:** Yes. `_apply_thread_automatics()` runs at line 550, then `_apply_thread_updates()` (record) runs at line 558. The ordering means automatics run *before* record updates. So:
1. Auto-dormant marks threads dormant (if 8+ turns without activity)
2. Record then updates those threads (potentially re-activating them)
3. Record wins because it runs last

**Risk:** Low. The ordering is correct — automatics are a safety net, record is the authoritative source. If record says "this thread is urgent", record wins. The dormant-urgency invariant (dormant → background) is enforced in automatics at line 181-191, which overrides any extractor that sets dormant threads to normal/urgent.

**Effort: LOW — 30 minutes**

Add a comment at line 547-554 clarifying the ordering rationale: "automatics run before record updates so they act as a safety net; record updates take precedence."

---

### INT-019 — Convergence score + EMA smoothing: first turn asymmetry

**Source:** `ccya/engine/narrate.py:219-236`

**Validated:** Yes. The EMA smoothing uses `prev_smoothed=0` on first turn, so `smoothed = 0.4 * raw`. The convergence hard gate uses the smoothed value, so the first turn can never trigger a forced RISING→CLIMAX transition via convergence.

**Risk:** Low. This is by design. The first turn is always special — no convergence history exists. The outcome_hint convergence hard gate at `_pacing.py:186-187` requires `config.convergence_enter_threshold` on smoothed, which is impossible on turn 1. This prevents premature phase transitions.

**Effort: NONE** — Correct behavior. Document it in the code comment.

---

### INT-036 — `_merge_arc_update()` unconditionally replaces threads[] and completed_threads[]

**Source:** `ccya/state/delta_builder.py:45-56`

**Validated:** Yes. `_merge_arc_update()` always replaces `threads` and `completed_threads` (lines 54-55). It's called from 5 places in `turn_state.py` (lines 552, 560, 619, 657, 698) and once in `apply_delta()` (line 283).

**Risk:** Medium-High. If any caller passes stale/empty data, the entire thread list gets wiped. All current callers are in `turn_state.py` and are careful to pass the current arc state with modifications. But a new caller added without understanding the "replace all" semantics could wipe threads.

**Effort: MEDIUM — 3 hours**

Add a safety check in `_merge_arc_update()`:
- If the input arc has 0 threads and the current arc has threads, log a warning
- Consider adding a "partial_update" mode that merges specific fields instead of replacing all
- Add a docstring clarifying the "replace all" semantics and the caller contract

---

### INT-068 — `_find_json()` shared by all LLM JSON parsing

**Source:** `ccya/engine/config.py:288-354`

**Validated:** Yes. 4-stage JSON extraction: (1) malformed key fixing via regex, (2) full-text parse, (3) code block extraction, (4) brace matching. Used by ruling.py:115, extraction/utils.py:181, thread_sanitizer.py:195, seed.py:293.

**Risk:** High blast radius. Every LLM JSON parsing in the engine goes through this. A bug here affects everything. However, it's well-tested with multiple fallback strategies.

**Effort: LOW — 2 hours**

Add logging when stage 0 regex fix is applied (line 303-310). This would help debug LLM output issues by logging when the regex fix changes the text. The fix is necessary for some LLMs but logging it would help identify which models produce malformed output.

---

### Summary

| # | Integration Point | Risk | Effort | Priority |
|---|-------------------|------|--------|----------|
| INT-071 | JSON coercion silent transformation | High | MEDIUM (4h) | P0 |
| INT-036 | Arc merge replaces all threads | Medium-High | MEDIUM (3h) | P1 |
| INT-047 | World state promotion when sanitizer disabled | Medium | LOW (2h) | P1 |
| INT-031 | Compendium dedup silent redirect | Medium | LOW (1h) | P2 |
| INT-017 | Beat leak after narrate | Low | LOW (30m) | P3 |
| INT-040 | Auto-dormant ordering | Low | LOW (30m) | P3 |
| INT-068 | JSON extraction no logging | High blast | LOW (2h) | P2 |
| INT-072 | Cross-stream dedup | Low | NONE | — |
| INT-030 | Post-delta context | Low | NONE | — |
| INT-019 | First turn convergence asymmetry | Low | NONE | — |


| # | From → To | What | How | File |
|---|-----------|------|-----|------|
| INT-001 | `turn.py` → `ruling.py` | Ruling phase invocation | `_ruling_phase(ctx)` returns intent, outcome, metrics | `turn.py:124` |
| INT-002 | `ruling.py` → `turn_context.py` | Ruling stores outcome/beat on context | `ctx.outcome`, `ctx._ages`, `ctx._selected_beat` | `ruling.py:196-204` |
| INT-003 | `turn.py` → `narrate.py` | Narration streaming | Generator yields phase/token events | `turn.py:168-174` |
| INT-004 | `narrate.py` → `_pacing.py` | Phase engine + convergence | `_compute_scene_phase()` + `compute_convergence_score()` | `narrate.py:224-242` |
| INT-005 | `turn.py` → `extraction/pipeline.py` | 3-stream extraction | `_run_extraction_pipeline()` returns merged delta | `turn.py:211-224` |
| INT-006 | `turn.py` → `turn_state.py` | Delta validation + apply | `_apply_state_updates()` returns state + rejected | `turn.py:238` |
| INT-007 | `turn.py` → `thread_sanitizer.py` | Async sanitize every N turns | `sanitize_threads()` returns corrected state | `turn.py:888-891` |
| INT-008 | `turn.py` → `world.py` | Async beat-candidate generation | `_run_world_step()` returns beat candidates | `turn.py:920-922` |
| INT-009 | `turn.py` → `changes.py` | State diff for UI display | `summarize_changes(pre, post, rejected)` | `turn.py:243` |
| INT-010 | `turn.py` → `state/io.py` | Persistence (state + events + chronicle) | `save_state()`, `append_event()`, `append_chronicle()` | `turn.py:54-61, 956-958` |

## 2. Ruling Phase (INT-011 to INT-017)

| # | From → To | What | How | File |
|---|-----------|------|-----|------|
| INT-011 | `ruling.py` → `_pacing.py` | Beat type validation from phase | `derive_allowed_beat_types(scene_phase, directive)` | `ruling.py:173, 212` |
| INT-012 | `ruling.py` → `npc_roster.py` | NPC roster for ruling prompt | `build_npc_roster(comp, turn_no)` | `ruling.py:170` |
| INT-013 | `ruling.py` → `extraction/utils.py` | PC situation filtering (persist only) | `_filter_pc_situation(pc.situation, schema)` | `ruling.py:18` |
| INT-014 | `ruling.py` → `rules.py` | Dice resolution (1d12+mod→band) | `resolve_check()` returns RulesOutcome | `ruling.py:248-259` |
| INT-015 | `ruling.py` → `_pacing.py` | Scene age computation | `_compute_ages(state)` → scene_age | `ruling.py:292-299` |
| INT-016 | `ruling.py` → `turn_context.py` | Beat selection from candidates | Reads `beat_candidates`, sets `pending_gm_beat`, pops | `ruling.py:204-227` |
| INT-017 | `turn.py` → `narrate.py` | Beat single-turn commitment | `pending_gm_beat` set by ruling, read/cleared by narrate | `turn.py:191-193` |

## 3. Narration Phase (INT-018 to INT-025)

| # | From → To | What | How | File |
|---|-----------|------|-----|------|
| INT-018 | `narrate.py` → `_pacing.py` | Pacing context computation | `_compute_pacing_context()` → directive + outcome_hint | `narrate.py:229-242` |
| INT-019 | `narrate.py` → `_pacing.py` | Convergence score + EMA smoothing | `compute_convergence_score()` → raw + smoothed | `narrate.py:210-221` |
| INT-020 | `narrate.py` → `hints.py` | Arc pressure score for hints | `compute_arc_pressure_score()` → score + hint_text | `narrate.py:73-94` |
| INT-021 | `narrate.py` → `npc_roster.py` | NPC roster for narration prompt | `build_npc_roster()` + `build_pending_roster_entries()` | `narrate.py:244-257` |
| INT-022 | `narrate.py` → `names.py` | Cultural name pool for new NPCs | `generate_npc_names_split()` seeded by turn | `narrate.py:163-172` |
| INT-023 | `narrate.py` → `_pacing.py` | Scene phase transition | `_compute_scene_phase()` returns new Scene, applied via `state.set_scene()` | `narrate.py:224` |
| INT-024 | `narrate.py` → `prompts/context.py` | Resolved arcs TTL filtering | `_get_resolved_arcs(state, turn_no, ttl)` | `narrate.py:142-150` |
| INT-025 | `narrate.py` → `turn.py` | PacingContext ↔ smoothed convergence | `_pc.convergence_score` set, `state.set_smoothed_convergence()` written | `narrate.py:240` |

## 4. Extraction Pipeline (INT-026 to INT-035)

| # | From → To | What | How | File |
|---|-----------|------|-----|------|
| INT-026 | `extraction/pipeline.py` → `scene.py` | Scene stream: NPC presence + location | `_extract_scene_messages()` → compendium_npc_update | `pipeline.py:290-310` |
| INT-027 | `extraction/pipeline.py` → `state.py` | State stream: inventory + conditions | `_extract_state_messages()` → inventory_add/remove/update | `pipeline.py:313-343` |
| INT-028 | `extraction/pipeline.py` → `record.py` | Record stream: threads + actions | `_record_messages()` → thread_update/resolve/add | `pipeline.py:346-394` |
| INT-029 | `extraction/record.py` → `narrate.py` | Cross-module: resolved arcs import | `from ccya.engine.narrate import _get_resolved_arcs` | `record.py:13` |
| INT-030 | `extraction/pipeline.py` → `context.py` | Post-delta virtual state for record | `_build_post_delta_context()` applies scene+state to state copy | `pipeline.py:353` |
| INT-031 | `extraction/pipeline.py` → `utils.py` | Compendium dedup (name matching) | `_dedup_compendium_update()` redirects IDs | `pipeline.py:200-252` |
| INT-032 | `extraction/scene.py` → `npc_roster.py` | NPC roster for scene extraction prompt | `build_npc_roster(comp, turn_no)` | `scene.py:21` |
| INT-033 | `extraction/state.py` → models | Intent from ruling in state prompt | `intent` param from `_extract_state_messages()` | `state.py:18, 37` |
| INT-034 | `extraction/record.py` → `prompts/context.py` | Thread formatting helpers | `_fmt_progress`, `_filter_completed_threads` | `record.py:15` |
| INT-035 | `extraction/utils.py` → `record.py` | Evicted thread filtering from history | `_filter_evicted_threads(prior_history, evicted_ids)` | `record.py:62-64` |

## 5. State Delta Application (INT-036 to INT-044)

| # | From → To | What | How | File |
|---|-----------|------|-----|------|
| INT-036 | `turn_state.py` → `delta_builder.py` | Arc update merging | `_merge_arc_update()` merges arc_update into live arc | `turn_state.py:552, 560, 619` |
| INT-037 | `turn_state.py` → `delta_builder.py` | Delta application (inventory/conditions/location) | `apply_delta(state, delta)` | `turn_state.py:497` |
| INT-038 | `delta_builder.py` → `npcs.py` | NPC scene management (upsert) | `apply_npc_scene_management()` creates/updates compendium | `delta_builder.py:270` |
| INT-039 | `npcs.py` → `npc_roster.py` | NPC color generation on creation | `generate_npc_color(nid)` | `npcs.py:53` |
| INT-040 | `turn_state.py` → `turn_state.py` | Auto-dormant + urgency decay | `_apply_thread_automatics()` → merged via `_merge_arc_update()` | `turn_state.py:550-554` |
| INT-041 | `turn_state.py` → models | Thread lifecycle from record result | `_apply_thread_updates()`, `_apply_thread_resolutions()`, `_apply_arc_resolve()` | `turn_state.py:557-666` |
| INT-042 | `turn_state.py` → `state/inventory.py` | Inventory ID resolution for removes | `resolve_inventory_remove_target()` | `turn_state.py:384` |
| INT-043 | `turn_state.py` → `world.py` | NPC presence decay (nearby→known, departed→archived) | `state.update_npc()` with presence changes | `turn_state.py:705-725` |
| INT-044 | `turn_state.py` → `npc_roster.py` | Color generation for new NPCs in delta | `generate_npc_color(cu.id)` | `turn_state.py:538` |

## 6. Thread Sanitizer (INT-045 to INT-048)

| # | From → To | What | How | File |
|---|-----------|------|-----|------|
| INT-045 | `thread_sanitizer.py` → `chronicle.py` | Sanitizer loads recent narration | `load_last_narration(save_dir, 5)` | `thread_sanitizer.py:59` |
| INT-046 | `thread_sanitizer.py` → models | LLM output validation against Pydantic | `_validate_parsed()` validates ThreadUpdate, ThreadResolution | `thread_sanitizer.py:214-322` |
| INT-047 | `turn_state.py` → `thread_sanitizer.py` | Two-step world state promotion | Record sets `world_state_candidate`, sanitizer promotes to `world_state` | `turn_state.py:345-352` |
| INT-048 | `turn.py` → `thread_sanitizer.py` | Sanitizer runs in async window | `sanitize_threads()` gated by `config.sanitize_every` | `turn.py:889` |

## 7. World Step (INT-049 to INT-052)

| # | From → To | What | How | File |
|---|-----------|------|-----|------|
| INT-049 | `world.py` → `_pacing.py` | Beat type filtering from phase | `derive_allowed_beat_types(scene_phase, directive)` | `world.py:52-55` |
| INT-050 | `world.py` → `npc_roster.py` | NPC roster for beat generation | `build_npc_roster()` filtered to present-only | `world.py:44-49` |
| INT-051 | `turn.py` → `world.py` | Pacing context → beat candidates | `pacing_context` in, `state.set_beat_candidates()` out | `turn.py:921-929` |
| INT-052 | `world.py` → models | Beat validation against GMBeat | `GMBeat(**entry)` | `world.py:140` |

## 8. Seed Generation (INT-053 to INT-055)

| # | From → To | What | How | File |
|---|-----------|------|-----|------|
| INT-053 | `seed.py` → `npc_roster.py` | Color generators for initial entities | `generate_npc_color()`, `generate_pc_color()`, `generate_item_color()` | `seed.py:86-93` |
| INT-054 | `seed.py` → `names.py` | Cultural name pools for PC/NPC/location | `generate_name_pool()`, `generate_npc_names()` | `seed.py:192-214` |
| INT-055 | `seed.py` → `pack.py` | Seed state envelope validation | `SeedStateEnvelope(**j)` with max 2 non-dormant threads, 1+ present NPC | `seed.py:335-458` |

## 9. Rules Engine (INT-056 to INT-057)

| # | From → To | What | How | File |
|---|-----------|------|-----|------|
| INT-056 | `rules.py` → models | Dice resolution → RulesOutcome | `resolve_check()` returns band, directive, dice stats | `rules.py:168-219` |
| INT-057 | `rules.py` → `narrate.py` | Directive from band + verb → outcome_hint | `build_directive(band, intent_verb, skill)` flows to pacing context | `rules.py:144-165` |

## 10. Pacing System (INT-058 to INT-060)

| # | From → To | What | How | File |
|---|-----------|------|-----|------|
| INT-058 | `_pacing.py` → `turn_context.py` | PacingContext dataclass across phases | `_compute_pacing_context()` → directive, outcome_hint, convergence | `_pacing.py:157-197` |
| INT-059 | `_pacing.py` → `turn.py` | `derive_allowed_beat_types()` in multiple places | Called in ruling validation, world filtering, event logging | `_pacing.py:36-52` |
| INT-060 | `_pacing.py` → `_pacing.py` | BEAT_BUCKETS for convergence beat_streak | `BEAT_BUCKETS["tension"]` in convergence computation | `_pacing.py:21-25` |

## 11. Hints / Pressure System (INT-061 to INT-062)

| # | From → To | What | How | File |
|---|-----------|------|-----|------|
| INT-061 | `hints.py` → models | Thread/arc pressure from age + progress | `compute_thread_pressure_score()`, `compute_arc_pressure_score()` | `hints.py:102-129` |
| INT-062 | `hints.py` → `prompts/context.py` | Progress formatting shared | `_fmt_progress()` formats ProgressEntry objects | `hints.py:52` |

## 12. Change Summarization (INT-063 to INT-064)

| # | From → To | What | How | File |
|---|-----------|------|-----|------|
| INT-063 | `changes.py` → models | State diff across inventory/player/facts/threads | `summarize_changes()` compares pre/post WorldState | `changes.py:75-302` |
| INT-064 | `changes.py` → `server/panels.py` | Emoji-formatted change lines for UI | `format_change_lines()` → display strings | `changes.py:305-384` |

## 13. Cross-Cutting Infrastructure (INT-065 to INT-072)

| # | From → To | What | How | File |
|---|-----------|------|-----|------|
| INT-065 | `config.py` → all engine modules | EngineConfig shared by every phase | Passed through TurnContext; read for temps, thresholds, TTLs | `config.py:27-126` |
| INT-066 | `config.py` → models | Config loading from YAML | `build_engine_config(cfg)` maps YAML keys to EngineConfig | `config.py:137-262` |
| INT-067 | `llm_client.py` → all LLM modules | LLM API client (retry, streaming, fallback) | `llm_chat()`, `llm_chat_stream()`, `trim_messages()` | `llm_client.py` |
| INT-068 | `config.py` → ruling/extraction/sanitize | Shared JSON extraction utility | `_find_json()` handles markdown fences, thinking tags | `config.py:288-354` |
| INT-069 | `state/utils.py` → `npc_roster.py` / `npcs.py` | Shared name utilities | `is_named()` heuristic, `strip_non_ascii()` | `npc_roster.py:9` |
| INT-070 | `state/inventory.py` → `delta_builder.py` | Inventory ID resolution | `resolve_inventory_canonical_id()`, `_fuzzy_match_inventory()` | `delta_builder.py:117-156` |
| INT-071 | `extraction/utils.py` → extraction | LLM output coercion | `_coerce_scene_json()` transforms raw JSON before validation | `extraction/utils.py:129-175` |
| INT-072 | `extraction/pipeline.py` → pipeline | Cross-stream dedup | `_dedup_compendium_update()` applied to both Add and Update arrays | `pipeline.py:200-252` |

---

## Summary by Category

| Category | Count |
|----------|-------|
| Turn Pipeline Orchestration | 10 |
| Ruling Phase | 7 |
| Narration Phase | 8 |
| Extraction Pipeline | 10 |
| State Delta Application | 9 |
| Thread Sanitizer | 4 |
| World Step | 4 |
| Seed Generation | 3 |
| Rules Engine | 2 |
| Pacing System | 3 |
| Hints / Pressure | 2 |
| Change Summarization | 2 |
| Cross-Cutting Infrastructure | 8 |
| **Total** | **72** |
