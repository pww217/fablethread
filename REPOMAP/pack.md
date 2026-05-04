# pack.py — world packs

## Public APIs

- **`load_pack(pack_id, packs_dir)`** → `Pack` — validates mode-specific files.
- **`list_packs(packs_dir)`** → `list[PackManifest]`.
- **`parse_world_facts(world_md)`** → `list[str]` — strips headings/bullets from world.md.

## Models

`PackManifest`, `PackFiles`, `Pack`, `SeedState`, `SeedEnvelope`, `ScenarioBrief`, `Constraints`, `Inspiration`, `PlayerOverrides`, `ExtractExample`.

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
