# Prompts — Jinja2 templates

## Template files

Located in `ccya/prompts/`:

- `rules_system.j2` / `rules_user.j2` — Call 0: intent classification + dice. `rules_system.j2` includes near-miss directive guidance: when a `fail` directive includes a near-miss note, the narration should describe a setback or complication that changes the situation without completely blocking the player.
- `narrate_system.j2` / `narrate_user.j2` — Call 1: prose narrative. `narrate_system.j2`: tense authority deferred to pack style block (defaults to past tense); inventory hard constraint rule prevents narrator from inventing items not in player's inventory. `narrate_user.j2`: inventory block labeled with cross-reference reminder.
- `extract_scene_system.j2` / `extract_scene_user.j2` — Call 2a: scene extraction. Novelty guard: `location_description` only emitted if narration adds NEW environmental details not in `## current_location_description`; default to null on uncertainty. ID guard: `location_change` only emitted when location ID actually changes; null when player stays in same location. Mandatory compendium pre-check: `npc_add` blocked for any NPC matching compendium entry by name/alias/bio/role; redirect to `npc_update` or skip. `scene_pressure_add` removed from schema/field rules (ownership migrated to progress extractor).
- `extract_state_system.j2` / `extract_state_user.j2` — Call 2b: state extraction. Generic item mapping rule: maps generic currency/item terms (coin, silver, gold piece, etc.) to canonical inventory IDs; never invents new IDs. Conditional `rules_stakes_hint` block injected when `stakes` and failure band present.
- `extract_progress_system.j2` / `extract_progress_user.j2` — Call 2c: progress extraction. Turn stamp injection via `## turn` block in user prompt + engine-side overwrite of `recent_events_add.turn`. Quest deduplication rule (MANDATORY) prevents near-duplicate quest creation with explicit "NEVER create" examples. Contact/meet objective rule is explicit override of general no-dice-roll completion guidance. `beat_disposition` and `scene_pressure_add` added to output schema + field rules. Progress user prompt: `stakes`/`band`/`deescalate`/`pending_beat`/`scene_pressure_add` instruction blocks injected before narration. Prior-turn index guard relaxed from `>= 2` to non-empty check.
- `generate_seed_system.j2` / `generate_seed_user.j2` — Seed generation for dynamic packs
- `generate_pack_system.j2` / `generate_pack_user.j2` — Pack generation from WorldBrief (used by `pack_gen.py`)
- `generate_pack_system_wb.j2` / `generate_pack_user_wb.j2` — Pack generation from world builder inputs (flat concept/tone_tags/world_rules)
- `compact_system.j2` / `compact_user.j2` — Chronicle compaction (LLM historian, PART 1: prior-history bullets, PART 2: state sanitization JSON with Pydantic-validated output contract, PART 3: recent_events consolidation — merge similar events, aim to halve count, in-universe phrasing, fresh IDs)

## Shared partials

Located in `ccya/prompts/sections/`:

- `_chronicle` — narrative history
- `_inventory` — player inventory
- `_location` — current location
- `_pc` — player character
- `_quests` — active quests only
- `_recent` — recent events
- `_recent_events` — event list
- `_world_state` — immutable world facts
