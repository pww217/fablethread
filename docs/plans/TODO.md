# CCYA TODO

Full plan details are in `plans/`. See `docs/ROADMAP.md` for priority phases.

---

## Completed Implementation Plans

- ~~**Module split refactor** — `engine.py`, `state.py`, `server.py` split into packages~~ — see `[completed/refactor-plan.md](completed/refactor-plan.md)`
- ~~**Context compactor** — chronicle bullet summaries, recent_events pruning, `compact_every` config~~ — see `[completed/compactor-plan.md](completed/compactor-plan.md)`
- ~~**Narrator-driven scope** — move scope decision from rules LLM to narrator post-narration; stream skipping + conditional templates; telemetry~~ — see `[completed/narrator-driven-scope.md](completed/narrator-driven-scope.md)`
- ~~**Compactor overhaul** — stable narrator window, `meta.prior_history` canonical store, corrected `last_compacted_turn` math, Pydantic-validated sanitization — see `[completed/compactor-overhaul.md](completed/compactor-overhaul.md)`

---

## P1 — Story Logical Consistency

### Context / Prompt Integrity

- ~~Fix `trim_messages` — truncate content instead of dropping messages~~
- ~~Audit and increase prompt token budget across all three streams~~
- ~~Context block labeling in `_chronicle.j2`, `_recent.j2`, `extract_user.j2`~~

### State Integrity

- ~~**recent_events ID-keyed overhaul** — `{id, text, turn}` objects, ID-based update/remove~~ — see `[p1-consistency/recent-events-overhaul.md](p1-consistency/recent-events-overhaul.md)`
- ~~**Entity deduplication** — canonical IDs for inventory/NPCs, alias registry, fuzzy safety net~~ — see `[p1-consistency/entity-dedup.md](p1-consistency/entity-dedup.md)`
- ~~**Remove condition TTL** — conditions cleared only by extractor~~ — see `[p1-consistency/condition-overhaul.md](p1-consistency/condition-overhaul.md)`
- ~~**Condition → skill feedback loop** — surface `rules_outcome.skill` + `band` + `directive` in extractor prompts~~ — see `[p1-consistency/condition-overhaul.md](p1-consistency/condition-overhaul.md)`
- ~~**Active-quest-only filter** — `_quests.j2` renders only active quests~~ — see `[p1-consistency/llm-pipeline-accuracy.md](p1-consistency/llm-pipeline-accuracy.md)`
- **Intent expansion** — extend `IntentEnvelope` with `active_domains`, `skip_domains`, `ambiguities`, `genre_note` — see `[p1-consistency/intent-expansion.md](p1-consistency/intent-expansion.md)`
- **Index system for inventory + NPCs** — replace slug references with sequential integers (`[0] Rusty Dagger`); engine owns index assignment and gap-close
- **Engine-owned quantity arithmetic** — LLM flags consumable/ammo usage; engine applies numeric delta

### Reconciliation

- ~~**Reconciliation system** — post-extraction pass: no item in both inventory and removed list~~ — see `[p1-consistency/reconciliation-system.md](p1-consistency/reconciliation-system.md)`

### Deferred

- ~~**Compaction redesign** — superseded by compactor~~ — see `[completed/compaction-strategy.md](completed/compaction-strategy.md)`
- ~~**Compactor** — superseded by completed compactor~~ — see `[completed/compactor-plan.md](completed/compactor-plan.md)`
- ~~**Compactor overhaul** — stable narrator window (`window_turns: 3`, `compact_every: 6`, `recent_turns_min: 2`), `meta.prior_history` canonical store, corrected `last_compacted_turn` math (root bug fix), Pydantic-validated sanitization (NPC dedup, inventory dedup, orphaned quest/pressure/condition cleanup), narrator no longer receives compacted turns — see `[compactor-overhaul.md](compactor-overhaul.md)`~~

> **Deferred from P1:** New-NPC compendium guarantee (LRU injection fix). Will be superseded
> by location-keyed NPC storage in a future milestone. The index system above is the intended
> interim fix for NPC slug hallucination until P4 lands. See `[p1-consistency/npc-compendium-guarantee.md](p1-consistency/npc-compendium-guarantee.md)`.

---

## P2 — Interesting Storytelling

- ~~**Band collapse to `partial`** — remove `mixed` + `boon`, add `partial` (finals 8–9)~~ — see `[completed/p2-inference/band-collapse.md](completed/p2-inference/band-collapse.md)`
- ~~**Verb-differentiated directives** — `build_directive()` branches on `_verb_category(intent_verb)`~~ — see `[completed/p2-inference/band-collapse.md](completed/p2-inference/band-collapse.md)`
- ~~**Momentum track** — `momentum: int` on PC state, directive at |momentum| >= 2~~ — see `[completed/p2-inference/momentum-track.md](completed/p2-inference/momentum-track.md)`
- ~~**Scene pressure** — `scene.scene_pressure` list, `ACTIVE THREATS` block in narrator~~ — see `[completed/p2-inference/scene-pressure.md](completed/p2-inference/scene-pressure.md)`
- ~~**Active DM / GM beat** — progress extractor emits `gm_beat`, narrator consumes next turn~~ — see `[completed/p2-inference/progress-dm-storytelling.md](completed/p2-inference/progress-dm-storytelling.md)`
- ~~**Scene age anti-stall** — track `scene.turn_entered`, nudge after N turns~~ — see `[completed/p2-inference/scene-age-anti-stall.md](completed/p2-inference/scene-age-anti-stall.md)`
- ~~**Band-scoped extract examples** — `pack_examples` conditioned on roll outcome band~~
- ~~**GM beat ownership migration: template fixes** — rules_user.j2 full narration, extract_progress_user.j2 recent_turns index, gm_beat instruction block — [`progress-rules-narration.md`](progress-rules-narration.md) (Phases 1–3 done)~~
- ~~**Narrative mechanics overhaul** — beat disposition (carry/replace/consume), scene_pressure_add migration to progress stream, stakes/band propagation to extractors, progress prompt context blocks — [`narrative-mechanics-overhaul.md`](narrative-mechanics-overhaul.md) (Phases 1–3 done)~~

---

## P3 — Inference Speed and Evaluation

- ~~**Eval harness** — Tier 1: `tests/test_engine_pipeline.py` with `_FakeLLM`; Tier 2: `make eval` with in-process driver, judge, REPORT.md~~ — see `[p3-inference/eval-harness.md](p3-inference/eval-harness.md)` and phase files `[p3-inference/eval-harness/0{1..7}-*.md](p3-inference/eval-harness/)`
- ~~**Eval improvement plan** — Rubric rewrite, context telemetry, new scenarios, Tier 1 schema validation~~ — see `[completed/eval_improvement_plan.md](completed/eval_improvement_plan.md)`
- ~~**Eval full-context trace** — Replace compact `build_trace()` with full-context trace including system prompts (per-turn), user prompts (per turn), world pack content, and state snapshots~~ — see `[completed/eval-full-context.md](completed/eval-full-context.md)`
- ~~**Phase 1: Trace/judge/report rewrite** — Full markdown traces, YAML front matter scoring, deterministic REPORT.md header, metadata event emission, dead config cleanup~~ — see `[p3-inference/eval-harness/08-trace-judge-report.md](p3-inference/eval-harness/08-trace-judge-report.md)`
- ~~**Phase 2: Dedup** — Sentinel markers in Jinja templates, `strip_trace_markers()` in engine, `_strip_immutable_sections`/`_diff_state_snapshots` in judge, `TraceOptions` config plumbing, `evals/config.yaml` trace knobs~~ — see `[completed/eval-engine-refactor.md](completed/eval-engine-refactor.md)` Phase 2
- ~~**Phase 3: Auto-checker** — `universal_asserts.py` with 5 cross-pipeline assertions, runner wiring, `build_trace` deterministic signals section, `_build_metrics_rows`, `engine_mirror` schema constants, rubric updates~~ — see `[completed/eval-engine-refactor.md](completed/eval-engine-refactor.md)` Phase 3
- ~~**Pipeline field routing remediation** — `eval-results-remediation/A-eval-results-remediation-pipeline-field-routing.md` — route `actions`/`outcome_summary` to progress extractor, `compendium_npc_update`/`scene_pressure_*`/`gm_beat` to scene extractor, remove `failed` from state extractor~~
- ~~**Scene pressure lifecycle rules** — `eval-results-remediation/B-eval-results-remediation-pressure-rules.md` — survival check for pressure removal, location-change guard, fixed-price transaction carve-out~~
- ~~**GM beat quality enforcement** — `eval-results-remediation/C-eval-results-remediation-gm-beat-enforcement.md` — Pydantic validator nullifies beats with blank/generic instructions, strengthened prompt rule requiring named entity~~
- ~~**Quest and state extraction fixes** — `eval-results-remediation/D-eval-results-remediation-quest-state-extraction.md` — contact/meet objective auto-completion, transfer-verb inventory domain trigger, NPC compendium dedup pre-pass~~
- ~~**Cleanup pass after Plans A–D** — `eval-results-remediation/E-eval-remediation-cleanup-pass.md` — comment out token-budget tests, remove `failed`/`last_turn_failed` plumbing, drop dead `quest_ages` loop, fix test fixtures, narration markers alignment, ARCHITECTURE.md + REPOMAP alignment~~
- ~~**Eval rubric and judge remediation** — `eval-results-remediation/E-eval-results-remediation-eval-rubric.md` — 7 weighted dimensions, anchored scores, auto-fail on empty gm_beat, mandatory synthesis, state-snapshot diff~~
- ~~**Eval system hardening Phase 01** — ARCHITECTURE.md restructure: 5-pipeline reference table, EVAL_CONTEXT delimiters, scrub frontend nodes~~ — see `[eval-results-remediation/eval-system-hardening.md](eval-results-remediation/eval-system-hardening.md)` Phase 01
- ~~**Eval system hardening Phase 02** — Pluggable packs: `pack_dirs` config, list-based search, runner accepts `packs_dirs`, evals/README.md~~ — see `[eval-results-remediation/eval-system-hardening.md](eval-results-remediation/eval-system-hardening.md)` Phase 02
- ~~**Eval system hardening Phase 03** — Multi-scenario CLI: default_scenario in config, --all flag, _run_one_scenario helper, Makefile eval-all target~~ — see `[eval-results-remediation/eval-system-hardening.md](eval-results-remediation/eval-system-hardening.md)` Phase 03
- ~~**Eval system hardening Phase 04** — Run-dir layout: events.jsonl + run.json into artifacts/, drop state.yaml, find_previous_run reads from artifacts/ with back-compat~~ — see `[eval-results-remediation/eval-system-hardening.md](eval-results-remediation/eval-system-hardening.md)` Phase 04
- ~~**Eval system hardening Phase 05** — Streaming REPORT.md: write_report_skeleton + append_judge_chunk + finalize_report; run_judge_streaming with on_chunk callback; CLI wires the three together~~ — see `[eval-results-remediation/eval-system-hardening.md](eval-results-remediation/eval-system-hardening.md)` Phase 05
- ~~**Eval system hardening Phase 06** — Architecture context loader: `ccya/eval/architecture_context.py` extracts EVAL_CONTEXT region from `docs/ARCHITECTURE.md` and prepends to judge system message~~ — see `[eval-results-remediation/eval-system-hardening.md](eval-results-remediation/eval-system-hardening.md)` Phase 06
- ~~**Eval system hardening Phase 07** — Prompt-redundancy detector: `ccya/eval/redundancy.py` compute_redundancy_signals + render_redundancy_section; wired into build_trace via _render_deterministic_signals~~ — see `[eval-results-remediation/eval-system-hardening.md](eval-results-remediation/eval-system-hardening.md)` Phase 07
- ~~**Eval system hardening Phase 08** — Compaction-feature signals: `ccya/eval/compaction_signals.py` with 14 enumerated capabilities; render_compaction_section appended to # Deterministic Signals~~ — see `[eval-results-remediation/eval-system-hardening.md](eval-results-remediation/eval-system-hardening.md)` Phase 08
- ~~**Eval system hardening Phase 09** — Universal asserts: fix `pending_gm_beat` path (`state.meta` not `state.scene`); add 5 new asserts (recent_events ring, NPC scene cap, condition dupes, actions count/distinct, momentum band delta)~~ — see `[eval-results-remediation/eval-system-hardening.md](eval-results-remediation/eval-system-hardening.md)` Phase 09
- ~~**Eval system hardening Phase 10** — Rubric refresh: rewrite `default.md` as Mechanical Design Critique + Storytelling Design Critique + Prompt Redundancy + Compaction Capabilities + Auto-Checker + Verdict + Recap; explicit Mechanic Placement subsection per pipeline~~ — see `[eval-results-remediation/eval-system-hardening.md](eval-results-remediation/eval-system-hardening.md)` Phase 10
- ~~**Eval run remediation #2** — `eval-results-remediation2/` — thinking suppression all pipelines (Phase 01 ✅), actions date plain text (Phase 02 ✅), narrator inventory binding rule (Phase 03 ✅), narrator tense conflict resolution (Phase 04 ✅), state extractor inventory mapping rule (Phase 05 ✅), progress turn stamp injection (Phase 06 ✅), quest deduplication rule (Phase 07 ✅), contact objective completion override (Phase 08 ✅), rules soft-fail/near-miss directive (Phase 09 ✅), scene location novelty guard (Phase 10 ✅), auto-checker NPC false-positive suppression (Phase 11 ✅) — see `[eval-results-remediation2/eval-result-remediation.md](eval-results-remediation2/eval-result-remediation.md)`~~

---

## P4 — World Continuity

- ~~**Custom world generator** — `generate_pack(WorldBrief)` → ScenarioBrief → Pack on disk; new schema (scenario.yaml absorbs world.md/style.md/factions/locations); extract_examples deleted; opening narrative quality pass; packs/default + packs/custom split — see [`completed/custom-world-gen.md`](completed/custom-world-gen.md)~~
- **Location-keyed NPC storage** — NPCs per location, LRU injection eliminated
- **Typed place pool generation** — settlements, taverns, districts, wilderness — see `[p4-world/world-prop-injection.md](p4-world/world-prop-injection.md)`
- **Organization/faction name pool** — seeded at game start, injected with political context — see `[p4-world/world-prop-injection.md](p4-world/world-prop-injection.md)`
- **Rumor pool** — template-filled rumors using seeded NPC names and places — see `[p4-world/world-prop-injection.md](p4-world/world-prop-injection.md)`
- **Object epithet pool** — named items for loot/discovery/combat — see `[p4-world/world-prop-injection.md](p4-world/world-prop-injection.md)`
- **Narrator prop injection rule** — prefer pool names over invented ones — see `[p4-world/world-prop-injection.md](p4-world/world-prop-injection.md)`
- **Locale-aware word lists by genre** — `pack.genre` selects `_WORD_LISTS_BY_GENRE` — see `[p4-world/world-prop-injection.md](p4-world/world-prop-injection.md)`
- **Character traits + relationships** — persist per NPC in compendium
- **Character avatars** — generated/assigned per NPC/PC
- **Physical descriptions** — generated at first encounter, stored in compendium

---

## Debug / Tooling

- ~~**Turn viewer dynamic mirror** — schema-driven tv.py; stream registry in `tv_mirror.py`; connectors from `sd.inputs`; scope block from narrator — see `[turn-viewer-dynamic.md](turn-viewer-dynamic.md)`~~

---

## Eval Remediation (May 2026)

See `[eval-remediation/findings-2026-05-09.md](eval-remediation/findings-2026-05-09.md)` for full findings.
See `[eval-remediation/01-extractor-grounding-and-compactor-fix.md](eval-remediation/01-extractor-grounding-and-compactor-fix.md)` for phased implementation plan.

- ~~**Fix compactor recent_events compaction** — ring buffer grows unbounded, no culling — see `[eval-remediation/compactor-recent-events.md](eval-remediation/compactor-recent-events.md)` for full spec~~
- ~~**Enforce quest deduplication** — progress extractor creates overlapping quest IDs instead of updating existing — see `[eval-remediation/quest-dedup.md](eval-remediation/quest-dedup.md)` for full spec~~
- ~~**Fix eval pack turn-0 start** — eval scenario should start at turn 0 for clean baseline — see `[eval-remediation/eval-pack-turn-0.md](eval-remediation/eval-pack-turn-0.md)` for full spec~~
- ~~**Fix scene extractor domain routing** — `eval-remediation/issues-4-8.md` Phase 1 — scene extractor skipped when compendium_npc active but scene/location_change not~~
- ~~**Fix generic item mapping in state extractor** — `eval-remediation/issues-4-8.md` Phase 2 — invents iron_coin instead of mapping to credits~~
- ~~**Strengthen scene extractor location_description nullification + npc_add compendium bloat** — `eval-remediation/issues-4-8.md` Phase 3 — redundant location descriptions, npc_add triggers compendium upserts for known NPCs~~
- ~~**Remove redundant style injection in narrate** — `eval-remediation/issues-4-8.md` Phase 4 — World Pack Style copied verbatim into narrate prompt~~
- ~~**Inventory item capitalization** — `eval-remediation/issues-4-8.md` Phase 5 — inventory items should start with a capital letter~~

- [ ] **Fix condition dedup** — extractor emits duplicate conditions, validator silently drops; add prompt directive + engine pre-filter — see `[eval-remediation/01-extractor-grounding-and-compactor-fix.md](eval-remediation/01-extractor-grounding-and-compactor-fix.md) Phase 1`
- ~~**Fix location change scope** — extractor emits location_change when only description changes; add ID-change guard to prompt — see `[eval-remediation/01-extractor-grounding-and-compactor-fix.md](eval-remediation/01-extractor-grounding-and-compactor-fix.md) Phase 2`~~
- ~~**Fix compendium NPC matching** — extractor creates duplicate IDs for known NPCs; extend dedup to npc_add + strengthen prompt — see `[eval-remediation/01-extractor-grounding-and-compactor-fix.md](eval-remediation/01-extractor-grounding-and-compactor-fix.md) Phase 3`~~
- ~~**Tune auto-checker false positives** — NER flags descriptors, inventory items, and PC names as unsanctioned NPCs — see `[eval-remediation/01-extractor-grounding-and-compactor-fix.md](eval-remediation/01-extractor-grounding-and-compactor-fix.md) Phase 4`~~
- [x] **Eval 13-turn expansion: dual compaction + gap coverage** — extend full_cycle from 10 to 13 turns, add combat/inventory/condition/removal turns, update rubric for dual compaction — see `[eval-13-turn-expansion.md](eval-13-turn-expansion.md)`

- [ ] **Compactor sanitization failure** — compactor fires at T6/T12 but LLM returns `{}` for all sanitization actions; quests not closed, pressures not removed — see `[eval-remediation-may10/01-eval-remediation-may10.md](eval-remediation-may10/01-eval-remediation-may10.md) Phase 1`
- [ ] **Narrator ignores player input** — Turn 7 narrator outputs stale context instead of processing input — see `[eval-remediation-may10/01-eval-remediation-may10.md](eval-remediation-may10/01-eval-remediation-may10.md) Phase 2`
- [ ] **Currency mapping failure (follow-up)** — state extractor still emits `iron_coins` instead of mapping to `credits` despite earlier fix; strengthened prompt directive needed — see `[eval-remediation-may10/01-eval-remediation-may10.md](eval-remediation-may10/01-eval-remediation-may10.md) Phase 3`

## Standalone

- [x] **`world_rules` — pack-level universe physical constants** — `ScenarioBrief.world_rules` (max 5), narrator `## Universe rules` block, seed context pass-through, pack-gen LLM instruction, `flooded-world` reference entries — see [`world-rules-backend-updates.md`](world-rules-backend-updates.md)
- [x] **World Builder UI — new game flow with custom world generation** — "Create Your Own" pack picker card → world builder 4-step form → SSE pack generation → char creator → begin game; new `generate_pack.py` engine module, `_world_builder.html` template, `/new-game/generate-pack` SSE endpoint — see [`world-builder-ui.md`](world-builder-ui.md)
- [x] **Pack deletion — delete custom/generated worlds from pack picker** — `DELETE /packs/{pack_id}` route, delete button on custom pack cards, confirmation dialog, JS re-wiring after deletion — see [`completed/pack-deletion.md`](completed/pack-deletion.md)
- [x] **Scene extractor scope reduction + narrative consolidation** — scene stream scoped to NPC presence, location change, scene tags/tagline, location_description only; pressure remove/update migrated to progress; update-only guard on scene_pressure_update; gm_beat entity-grounding rule — see [`scene-progress-fixes.md`](scene-progress-fixes.md)

