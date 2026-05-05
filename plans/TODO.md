# CCYA TODO

Full plan details are in `plans/`. See `docs/ROADMAP.md` for priority phases.

---

## P1 — Story Logical Consistency

### Context / Prompt Integrity

- ~~Fix `trim_messages` — truncate content instead of dropping messages; never drop `system` role~~
- ~~Audit and increase prompt token budget across all three streams~~
- ~~Context block labeling: `## PRIOR HISTORY` wrapper in `_chronicle.j2`, `## RECENT TURNS` in `_recent.j2`, `## CURRENT TURN NARRATION` label in `extract_user.j2`~~

### State Integrity

- `**recent_events` ID-keyed overhaul** — replace string list with `{id, text, turn}` objects; extractor uses IDs for update/remove; exact ID comparison replaces fuzzy norm in `summarize_changes()`; `_fact_in_list`/`_norm_fact` in engine.py deleted. See `plans/recent-events-overhaul.md`
- **Entity deduplication** — canonical `snake_case` IDs for inventory and NPCs at creation; extractor match instruction checks existing state before adding; NPC alias registry (`aliases: list[str]`) on compendium entries; engine alias map + fuzzy token-overlap safety net (pure Python). See `plans/entity-dedup.md`
- ~~**Remove condition TTL** — delete `CONDITION_TTL_TURNS`, `condition_ttl_turns` config, and the engine pre-extraction loop; conditions cleared only by extractor. See `plans/condition-overhaul.md`~~
- ~~**Condition → skill feedback loop** — surface `rules_outcome.skill` + `band` + `directive` in `extract_state_user.j2`; add condition-trigger guidance keyed to failing skill in both `extract_state_system.j2` and `extract_state_user.j2`. See `plans/condition-overhaul.md`~~
- ~~**Active-quest-only filter** — `_quests.j2` renders only quests with `status: active`; completed/failed quests go to compaction chronicle. See `plans/p1-consistency/llm-pipeline-accuracy.md`~~
- **Intent expansion** — extend `IntentEnvelope` with `active_domains`, `skip_domains`, `ambiguities`, `genre_note`; wire domains into extractor context, ambiguities into narrator context. See `plans/intent-expansion.md`

### Reconciliation

- ~~**Reconciliation system** — post-extraction pass: no item in both inventory and removed list, no duplicate IDs. See `plans/reconciliation-system.md`~~

### Deferred

- **Compaction redesign** — token-threshold trigger, new `compact_system.j2` + `compact_user.j2`, engine archive logic. See `plans/compaction-strategy.md`

> **Deferred from P1:** New-NPC compendium guarantee (LRU injection fix). Will be superseded
> by location-keyed NPC storage in a future milestone. See `plans/npc-compendium-guarantee.md`.

---

## P2 — Interesting Storytelling

- **Band collapse to `partial`** — remove `mixed` + `boon` from `GM_MOVES` and `compute_band()`; add `partial` (finals 8–9). See `plans/band-collapse.md`
- **Verb-differentiated directives** — `build_directive()` branches on `_verb_category(intent_verb)` with per-`(band, category)` directive table. See `plans/band-collapse.md`
- **Momentum track** — add `momentum: int` to PC state; `apply_momentum()` in `engine.py` after rules resolves; inject directive into `narrate_user.j2` at |momentum| >= 2. Depends on band collapse. See `plans/momentum-track.md`
- **Scene pressure** — `scene.scene_pressure` list separate from `world_state`; extractor adds/removes pressure entries; narrator gets `ACTIVE THREATS` block. See `plans/scene-pressure.md`
- **Active DM / GM beat** — progress extractor emits `gm_beat`; engine stores as `pending_gm_beat` in meta; narrator consumes on next turn. See `plans/progress-dm-storytelling.md`
- **Scene age anti-stall** — track `scene.turn_entered`; after N turns in same location, narrator gets a nudge to advance or change the scene. See `plans/p2-storytelling/scene-age-anti-stall.md`
- **Band-scoped extract examples** — `pack_examples` conditioned on actual roll outcome band; show extractor what a `fail` extraction looks like vs. `crit_success`

---

## P3 — Inference Speed

- **Prompt trimming through pipeline** — replace `recent_turns` prose with compact `{turn, band, directive, scene_tagline}`; move static data to system prompt; audit and drop unused Rules output fields. See `plans/p3-inference/prompt-optimization.md`
- **Static/dynamic prompt split audit** — identify all prompt content that never changes turn-to-turn; move to system message for KV-cache benefit. See `plans/p3-inference/prompt-optimization.md`
- **Per-call token instrumentation** — log prompt/completion tokens per stream per turn; surface in debug UI. See `plans/p3-inference/prompt-optimization.md`
- **KV-cache pinning** — ensure system prompts are stable strings eligible for provider-side KV caching. See `plans/p3-inference/prompt-optimization.md`
- **Model-agnostic thinking infra** — abstract reasoning/thinking config so it works across Anthropic, Gemini, and local models. See `plans/p3-inference/prompt-optimization.md`
- **Dev mode dual-model setup** — cheap fast model for dev iteration, production model behind a flag. See `plans/p3-inference/prompt-optimization.md`

---

## P4 — World Continuity

- **Location-keyed NPC storage** — NPCs stored per location, not flat compendium; LRU injection eliminated; mobile NPC `currently_at` override. Replaces NPC compendium guarantee. See `plans/p4-world/npc-location-storage.md`
- **Typed place pool generation** — `generate_place_pool()` in `names.py`; settlements, taverns, districts, wilderness. See `plans/world-prop-injection.md`
- **Organization/faction name pool** — seeded at game start, injected into narrate prompt when political context is present. See `plans/world-prop-injection.md`
- **Rumor pool** — template-filled rumors using seeded NPC names and places; injected into social narration as `AVAILABLE RUMORS`. See `plans/world-prop-injection.md`
- **Object epithet pool** — named items pool for loot/discovery/combat turns. See `plans/world-prop-injection.md`
- **Narrator prop injection rule** — add rule to `narrate_system.j2` instructing narrator to prefer pool names over invented ones. See `plans/world-prop-injection.md`
- **Locale-aware word lists by genre** — `pack.genre` flag selects appropriate `_WORD_LISTS_BY_GENRE` entry. See `plans/world-prop-injection.md`
- **Character traits + relationships** — persist trait list and relationship map per NPC in compendium. See `plans/p4-world/npc-location-storage.md`
- **Character avatars** — generated or assigned avatar per NPC/PC, stored in compendium. See `plans/p4-world/npc-location-storage.md`
- **Physical descriptions** — generated physical description per NPC at first encounter, stored in compendium. See `plans/p4-world/npc-location-storage.md`

