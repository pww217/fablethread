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

- ~~**Band collapse to `partial**` — remove `mixed` + `boon`, add `partial` (finals 8–9)~~ — see `[completed/p2-inference/band-collapse.md](completed/p2-inference/band-collapse.md)`
- ~~**Verb-differentiated directives** — `build_directive()` branches on `_verb_category(intent_verb)`~~ — see `[completed/p2-inference/band-collapse.md](completed/p2-inference/band-collapse.md)`
- ~~**Momentum track** — `momentum: int` on PC state, directive at |momentum| >= 2~~ — see `[completed/p2-inference/momentum-track.md](completed/p2-inference/momentum-track.md)`
- ~~**Scene pressure** — `scene.scene_pressure` list, `ACTIVE THREATS` block in narrator~~ — see `[completed/p2-inference/scene-pressure.md](completed/p2-inference/scene-pressure.md)`
- ~~**Active DM / GM beat** — progress extractor emits `gm_beat`, narrator consumes next turn~~ — see `[completed/p2-inference/progress-dm-storytelling.md](completed/p2-inference/progress-dm-storytelling.md)`
- ~~**Scene age anti-stall** — track `scene.turn_entered`, nudge after N turns~~ — see `[completed/p2-inference/scene-age-anti-stall.md](completed/p2-inference/scene-age-anti-stall.md)`
- ~~**Band-scoped extract examples** — `pack_examples` conditioned on roll outcome band~~

---

## P3 — Inference Speed and Evaluation

- ~~**Eval harness** — Tier 1: `tests/test_engine_pipeline.py` with `_FakeLLM`; Tier 2: `make eval` with in-process driver, judge, REPORT.md~~ — see `[p3-inference/eval-harness.md](p3-inference/eval-harness.md)` and phase files `[p3-inference/eval-harness/0{1..7}-*.md](p3-inference/eval-harness/)`
- ~~**Eval improvement plan** — Rubric rewrite, context telemetry, new scenarios, Tier 1 schema validation~~ — see `[completed/eval_improvement_plan.md](completed/eval_improvement_plan.md)`
- ~~**Eval full-context trace** — Replace compact `build_trace()` with full-context trace including system prompts (per-turn), user prompts (per turn), world pack content, and state snapshots~~ — see `[completed/eval-full-context.md](completed/eval-full-context.md)`

---

## P4 — World Continuity

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

- **Turn viewer dynamic mirror** — schema-driven tv.py; stream registry in `tv_mirror.py`; connectors from `sd.inputs` — see `[turn-viewer-dynamic.md](turn-viewer-dynamic.md)`

