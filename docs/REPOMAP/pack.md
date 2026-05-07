# pack.py — world packs

## Public APIs

- **`load_pack(pack_id, packs_dir)`** → `Pack` — validates mode-specific files.
- **`list_packs(packs_dir)`** → `list[PackManifest]`.
- **`parse_world_facts(world_md)`** → `list[str]` — strips headings/bullets from world.md.

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
- `Constraints` — `min_named_npcs` (2), `min_objectives_per_quest` (2), `starting_quest_count` (1), `inventory_size_range` (4,8), `pc_stat_range` (1,4), `pc_stat_total_range` (12,18), `prose_word_range` (200,500), `required_inventory_kinds`, `npc_distinct_first_letters` (True), `forbid_cliches`, `forbid_player_dependents` (True), `forbid_legendary_items` (True)
- `Inspiration` — `pc`, `opening_situation`, `npcs`, `inventory`, `quests` (all default "")
- `ScenarioBrief` — `constraints` (Constraints), `inspiration` (Inspiration)
- `PlayerOverrides` — `pc_hints`, `npc_hints`, `location_hints`, `quest_hints`, `free_form` (all default ""), `npc_count` (0 = use pack default). Has `is_empty()` method.
- `ExtractExample` — `title`, `band` (default ""), `thinking` (default ""), `json_text` (alias "json", validated as valid JSON). `populate_by_name: True`.
- `PackFiles` — `seed | None`, `opening | None`, `world | None`, `scenario | None`, `style | None`, `extract_examples | None`
- `PackManifest` — `id`, `name`, `description` (default ""), `genre` (default ""), `tone_tags` (list[str]), `version` (int, default 1), `mode` (Literal["static", "dynamic"]), `files` (PackFiles), `baseline_facts` (max 3), `name_locales` (list[dict])
- `Pack` — `manifest` (PackManifest), `style_text` (default ""), `extract_examples` (list[ExtractExample]), `seed | None`, `opening_text` (default ""), `opening_actions` (list[str]), `world_text` (default ""), `scenario | None`. Has `_check_mode_files` validator (static requires seed + opening_text; dynamic requires world_text + scenario).

## Pack structure

Each pack in `packs/{pack_id}/`:

**Static mode** (hand-authored seed):
- `pack.yaml` (mode: static) + `seed_state.yaml` + `opening_scene.md`
- Optional: `style.md`, `extract_examples.yaml`

**Dynamic mode** (LLM-generated seed):
- `pack.yaml` (mode: dynamic) + `world.md` + `scenario.yaml`
- Optional: `style.md`, `extract_examples.yaml`

`pack.yaml` fields: `id`, `name`, `description`, `genre`, `tone_tags`, `version`, `mode`, `files` (maps to filenames), `baseline_facts` (hardcoded genre canon, max 3), `name_locales` (weighted Faker locales).

## Name generation (names.py)

- **`generate_name_pool(locales, pc_count, npc_count, location_count, seed)`** → `{"pc": [...], "npc": [...], "location": [...]}` — culturally-appropriate name pools via Faker.
- **`generate_npc_names(locales, count, seed)`** → `list[str]` — NPC name candidates for mid-game injection.
- Names drawn with probability proportional to each locale's weight. Falls back to en_US if locales empty.
