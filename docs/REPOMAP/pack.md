# pack.py — world packs

## Public APIs

- **`load_pack(pack_id, packs_dir)`** → `Pack` — validates pack has either seed_state.yaml (static) or scenario.yaml (generated). Accepts namespaced slugs `"default/foo"` or `"custom/bar"`.
- **`list_packs(packs_dir)`** → `list[PackManifest]` — aggregates from `packs/default/` and `packs/custom/`.
- **`parse_world_facts(world_md)`** → `list[str]` — strips headings/bullets from world.md.
- **`_resolve_pack_dir(pack_id, packs_dir)`** → `Path` — resolves bare slug (searches default/, custom/) or namespaced slug.

## Engine integration

- **`generate_pack(brief: WorldBrief, config: EngineConfig, packs_dir: Path, *, template_dir, max_retries)`** → `Pack` (async) — defined in `ccya/engine/pack_gen.py`. Takes player concept input, generates complete `ScenarioBrief` via LLM, writes `pack.yaml` + `scenario.yaml` to `packs/custom/<slug>/`, returns loaded `Pack`. Uses `generate_pack_system.j2` + `generate_pack_user.j2` prompts.

## Models

- `SeedPC` — `name`, `tagline` (default ""), `bio` (default ""), `stats` (dict[str, int]), `conditions` (list[str]), `momentum` (int, default 0). Has `_migrate_concept` validator (migrates old `concept` → `tagline`).
- `SeedLocation` — `id`, `name`, `description` (default "")
- `SeedQuestObjective` — `description`, `done` (default False), `failed` (default False)
- `SeedQuest` — `id`, `title`, `status` (default "active"), `objectives` (list[SeedQuestObjective])
- `CompendiumEntry` — `name | None`, `title | None`, `bio | None`. `extra: "allow"`
- `SeedCompendium` — `npcs: dict[str, CompendiumEntry]`
- `SeedScene` — `tagline` (default ""), `tags` (list[str]), `world_state` (list[str]), `recent_events` (list[str]), `present_npcs` (list[dict])
- `SeedState` — `meta` (dict[str, Any]), `pc` (SeedPC), `location` (SeedLocation), `inventory` (list[InventoryItem], 1–12 items), `quests` (list[SeedQuest], min 1), `scene` (SeedScene), `compendium` (SeedCompendium)
- `SeedEnvelope` — `seed_state` (SeedState), `opening_narrative` (min 50 chars), `actions` (exactly 4 strings)
- `Faction` — `id` (snake_case), `name`, `description`, `disposition` ("neutral" | "hostile" | "friendly", default "neutral")
- `NamedLocation` — `id` (snake_case), `name`, `type` (settlement | ruin | wilderness | transit | institution), `description`
- `Constraints` — `min_named_npcs` (2), `min_objectives_per_quest` (2), `starting_quest_count` (1), `inventory_size_range` (4,8), `pc_stat_range` (1,4), `pc_stat_total_range` (12,18), `prose_word_range` (200,500), `required_inventory_kinds`, `npc_distinct_first_letters` (True), `forbid_cliches`, `forbid_player_dependents` (True), `forbid_legendary_items` (True)
- `Inspiration` — `pc`, `opening_situation`, `npcs`, `inventory`, `quests` (all default "")
- `ScenarioBrief` — `constraints` (Constraints), `world_facts` (max 8 strings, replaces world.md), `narrator_rules` (max 12 strings, replaces style.md), `world_rules` (max 5 strings, hard physical laws rendered as `## Universe rules` block in narrator prompt), `factions` (max 6 Faction objects, injected into narrate context), `locations` (max 10 NamedLocation objects, injected into narrate context), `name_locales` (list[dict] for Faker), `name_seed` (int, 0 = randomized), `inspiration` (Inspiration). Old-format scenario.yaml (only constraints + inspiration) still validates — new fields default to empty.
- `WorldBrief` — `concept` (required, the pitch), `tone`, `geography`, `power`, `daily_life`, `player_hint` (all default ""). Input contract for `generate_pack()`.
- `GeneratedPackMeta` — `generated` (True), `world_brief_concept` (default ""). Provenance marker for generated packs.
- `PlayerOverrides` — `pc_hints`, `npc_hints`, `location_hints`, `quest_hints`, `free_form` (all default ""), `npc_count` (0 = use pack default). Has `is_empty()` method.
- `PackManifest` — `id`, `name`, `description` (default ""), `genre` (default ""), `tone_tags` (list[str]), `baseline_facts` (max 3), `name_locales` (list[dict]). `extra: "ignore"` — silently passes unknown keys (e.g. old `mode`, `version`, `files`).
- `Pack` — `manifest` (PackManifest), `world_text` (default "", legacy world.md), `style_text` (default "", legacy style.md), `seed | None` (static mode), `opening_text` (default ""), `opening_actions` (list[str]), `scenario | None` (generated mode, contains world_facts, narrator_rules, factions, locations, name_locales, name_seed). Has `_check_playable` validator (requires seed OR scenario). Has `mode` property ("static" or "dynamic").

## Pack structure

Each pack in `packs/{namespace}/{pack_id}/` (namespace = `default` or `custom`):

**Static mode** (hand-authored seed):
- `pack.yaml` + `seed_state.yaml` + `opening_scene.md`
- Optional: `style.md`

**Generated mode** (LLM-generated seed):
- `pack.yaml` + `scenario.yaml`
- Optional: `style.md` (legacy fallback)

`pack.yaml` fields: `id`, `name`, `description`, `genre`, `tone_tags`, `baseline_facts` (hardcoded genre canon, max 3), `name_locales` (weighted Faker locales). Old fields (`mode`, `version`, `files`) are silently ignored.

`scenario.yaml` fields (new consolidated schema): `constraints`, `world_facts` (3-8 durable facts), `narrator_rules` (6-12 behavioral rules), `world_rules` (0-5 hard physical laws), `factions` (3-6 Faction objects), `locations` (4-10 NamedLocation objects), `name_locales`, `name_seed`, `inspiration`. Replaces `world.md` + `style.md` + `pack.yaml` locale/facts fields.

## Name generation (names.py)

- **`generate_name_pool(locales, pc_count, npc_count, location_count, seed)`** → `{"pc": [...], "npc": [...], "location": [...]}` — culturally-appropriate name pools via Faker.
- **`generate_npc_names_split(locales, male_count, female_count, seed)`** → `{"male": [...], "female": [...]}` — gender-split name pool for narrate context.

## Engine integration (seed.py)

- `generate_seed()` sources `world_facts` from `scenario.world_facts` (new) → `manifest.baseline_facts` → `parse_world_facts(world.md)` (legacy). Raises `ValueError` on static packs. Normalizes `active_threads[*].state` to `active` after copying arc from envelope.
- `_build_generate_seed_messages()` passes `name_seed` (randomized if `scenario.name_seed` is 0) to `generate_seed_user.j2`.
- `generate_seed_user.j2` renders `scenario.world_facts`, `scenario.narrator_rules`, `scenario.world_rules`, `scenario.factions`, `scenario.locations`, `name_seed`, `scenario.inspiration`, `player_overrides`, and `name_pool`.
- **`generate_npc_names(locales, count, seed)`** → `list[str]` — NPC name candidates for mid-game injection.
- Names drawn with probability proportional to each locale's weight. Falls back to en_US if locales empty.
