# CCYA TODO

Full plan details are in `plans/`. See `docs/ROADMAP.md` for priority phases.

---

## P1 — Story Logical Consistency

### Context / Prompt Integrity
- [ ] Fix `trim_messages` — truncate content instead of dropping messages; never drop `system` role
- [ ] Audit and increase prompt token budget across all three streams
- [ ] Context block labeling (Plan A): `## PRIOR HISTORY` wrapper in `_chronicle.j2`, `## RECENT TURNS` in `_recent.j2`, `## CURRENT TURN NARRATION` label in `extract_user.j2`
- [ ] Compaction redesign (Plan F): token-threshold trigger, new `compact_system.j2` + `compact_user.j2`, engine archive logic. See `plans/llm-pipeline-accuracy.md`

### State Integrity
- [ ] **`recent_events` ID-keyed overhaul** — replace string list with `{id, text, turn}` objects; delete `_fact_in_list` / `_norm_fact`; update `apply_delta`, templates, and migration helper. See `plans/recent-events-overhaul.md`
- [ ] **Canonical inventory IDs** — every item gets a stable snake_case ID at creation; extractor uses IDs for update/remove, never name-matching
- [ ] **NPC alias deduplication** — compendium upsert checks aliases before creating a new entry; extractor instructed to match by alias before emitting a new NPC
- [ ] **Remove condition TTL** — delete `CONDITION_TTL_TURNS`, `condition_ttl_turns` config, and the engine pre-extraction loop; conditions cleared only by extractor. See `plans/condition-overhaul.md`
- [ ] **Condition → skill feedback loop** — surface `rules_outcome.skill` + `band` + `directive` in `extract_state_user.j2`; add condition-trigger guidance keyed to failing skill. See `plans/condition-overhaul.md`
- [ ] **Active-quest-only filter** — `_quests.j2` renders only quests with `status: active`; completed/failed quests go to compaction chronicle
- [ ] **Fix present/recently-left contradiction** — engine validates `present_npcs` against `recently_left` before applying delta; mutual exclusion enforced
- [ ] **New-NPC compendium guarantee** — `present_npcs` in current scene always gets full compendium rows (or explicit empty row signaling new NPC), regardless of LRU recency. See previous conversation.

### Reconciliation
- [ ] **Reconciliation system** — post-extraction pass that checks internal state consistency: no item in both inventory and removed list, no NPC in both present and recently_left, no duplicate fact IDs

---

## P2 — Interesting Storytelling

- [ ] **Momentum track** — add `momentum: int` to PC state; `apply_momentum()` in `engine.py` after rules resolves; inject directive into `narrate_user.j2` at |momentum| >= 2. See `plans/momentum-track.md`
- [ ] **Scene pressure** — add `scene.scene_pressure: list[ScenePressure]` separate from `world_state`; extractor adds/removes pressure entries; narrator gets `ACTIVE THREATS` block. See `plans/scene-pressure.md`
- [ ] **Active DM / GM beat** — progress extractor emits `gm_beat` after extraction; engine stores as `pending_gm_beat` in meta; narrator consumes on next turn. See `plans/progress-dm-storytelling.md`
- [ ] **Band collapse to `partial`** — remove `mixed` + `boon` from `GM_MOVES` and `compute_band()`; add `partial` (finals 8–9). See `plans/band-collapse.md`
- [ ] **Verb-differentiated directives** — `build_directive()` branches on `_verb_category(intent_verb)` with per-`(band, category)` directive table. See `plans/band-collapse.md`
- [ ] **Scene age anti-stall** — track `scene.turn_entered`; after N turns in same location, narrator gets a nudge to advance or change the scene
- [ ] **Band-scoped extract examples** — `pack_examples` conditioned on actual roll outcome band; show extractor what a `fail` extraction looks like vs. `crit_success`

---

## P3 — Inference Speed

- [ ] **Replace `recent_turns` prose with `outcome_summary`** — compact `{turn, band, directive, scene_tagline}` instead of full narrative text in rolling context
- [ ] **Move `world_state` + `name_pool` to system prompt** — static per-session data should not repeat in every user message
- [ ] **Remove unused Rules output fields** — audit `target`, `stakes`, `check.tags` — drop anything not consumed downstream
- [ ] **Static/dynamic prompt split audit** — identify all prompt content that never changes turn-to-turn; move to system message for KV-cache benefit
- [ ] **Per-call token instrumentation** — log prompt/completion tokens per stream per turn; surface in debug UI
- [ ] **KV-cache pinning** — ensure system prompts are stable strings eligible for provider-side KV caching
- [ ] **Model-agnostic thinking infra** — abstract reasoning/thinking config so it works across Anthropic, Gemini, and local models
- [ ] **Dev mode dual-model setup** — cheap fast model for dev iteration, production model behind a flag

---

## P4 — World Continuity

- [ ] **Typed place pool generation** — `generate_place_pool()` in `names.py`; settlements, taverns, districts, wilderness; stored in seed manifest. See `plans/world-prop-injection.md`
- [ ] **Organization/faction name pool** — seeded at game start, injected into narrate prompt when political context is present. See `plans/world-prop-injection.md`
- [ ] **Rumor pool** — template-filled rumors using seeded NPC names and places; injected into social narration as `AVAILABLE RUMORS`. See `plans/world-prop-injection.md`
- [ ] **Object epithet pool** — named items pool for loot/discovery/combat turns. See `plans/world-prop-injection.md`
- [ ] **Narrator prop injection rule** — add rule to `narrate_system.j2` instructing narrator to prefer pool names over invented ones. See `plans/world-prop-injection.md`
- [ ] **Locale-aware word lists by genre** — `pack.genre` flag selects appropriate `_WORD_LISTS_BY_GENRE` entry. See `plans/world-prop-injection.md`
- [ ] **Character traits + relationships** — persist trait list and relationship map per NPC in compendium
- [ ] **Character avatars** — generated or assigned avatar per NPC/PC, stored in compendium
- [ ] **Physical descriptions** — generated physical description per NPC at first encounter, stored in compendium
