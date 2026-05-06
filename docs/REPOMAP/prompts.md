# Prompts — Jinja2 templates

## Template files

Located in `ccya/prompts/`:

- `rules_system.j2` / `rules_user.j2` — Call 0: intent classification + dice
- `narrate_system.j2` / `narrate_user.j2` — Call 1: prose narrative
- `extract_scene_system.j2` / `extract_scene_user.j2` — Call 2a: scene extraction
- `extract_state_system.j2` / `extract_state_user.j2` — Call 2b: state extraction
- `extract_progress_system.j2` / `extract_progress_user.j2` — Call 2c: progress extraction
- `generate_seed_system.j2` / `generate_seed_user.j2` — Seed generation for dynamic packs

## Shared partials

Located in `ccya/prompts/sections/`:

- `_chronicle` — narrative history
- `_inventory` — player inventory
- `_location` — current location
- `_pc` — player character
- `_quests` — active quests
- `_recent` — recent events
- `_recent_events` — event list
- `_world_state` — immutable world facts
