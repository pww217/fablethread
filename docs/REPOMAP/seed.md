# seed.py — dynamic seed generation

## Public APIs

- **`generate_seed(pack, config, *, overrides, seed, template_dir)`** → `SeedEnvelope` (async) — generates a fresh game seed via LLM. Sources `world_facts` from `scenario.world_facts` → `manifest.baseline_facts` → `parse_world_facts(world.md)`. Raises `ValueError` on static packs. Retries on parse/validation failure up to `config.generate_seed_max_retries`.

## Internal functions

- **`_strip_non_ascii(text)`** → `str` — removes non-ASCII characters from text using regex.
- **`_sanitize_envelope(envelope)`** → `SeedEnvelope` — strips non-ASCII from all name fields (PC, NPC, location, inventory, quests, scene, compendium, opening_narrative, actions).
- **`_validate_seed_envelope(envelope)`** → `None` — raises `ValueError` if `envelope.seed_state.pc.name` has fewer than 2 whitespace-separated tokens (enforces first+last name requirement). Called immediately after `_sanitize_envelope` in `generate_seed`.
- **`_build_generate_seed_messages(env, pack, overrides)`** → `list[dict]` — builds system+user messages for the seed LLM call. Passes `name_seed` (randomized if 0), `name_pool`, `scenario` fields, `player_overrides`.
- **`_soft_validate_seed(envelope, pack, overrides)`** → `list[str]` — returns soft validation warnings (word count, forbidden cliches, player-dependent relationships). Does not raise.

## Engine integration

- `generate_seed()` calls `_build_generate_seed_messages()` → `trim_messages()` → LLM chat → `_find_json()` → `SeedEnvelope(**j)` → `_sanitize_envelope()` → `_validate_seed_envelope()` → injects baseline_facts into `world_state` → clears `compendium_touch_order` → seeds faction/location pools → runs `_soft_validate_seed()` → returns envelope.
- Prompt templates: `generate_seed_system.j2` (PC name constraint, starter inventory rules, world_state/recent_events discipline, quest design constraint), `generate_seed_user.j2` (scenario facts, factions, locations, name pool, player overrides).
