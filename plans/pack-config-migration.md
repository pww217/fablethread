# Pack-Specific Config Migration + Pool Conversion

## Status
`open`

## Phases

5 phases covering: (1) manifest schema additions for genre-specific config, (2) seed.py refactor to read from manifests instead of hardcoded lists, (3-5) populate space-western/sengoku-japan/allied-ww2 packs with pool data and strip old-style inspiration.

## Issue

Genre/game-specific configuration is split between two places: `ccya/engine/seed.py` contains `_GENRE_TAG_WHITELIST`, `_HISTORICAL_COMBAT`, and `_normalize_genre_key()` — all hardcoded per-genre constants that should be pack-declared metadata. This violates the principle that engine code should only contain core-agnostic logic, and it blocks converting space-western/sengoku-japan/allied-ww2 to pool format since these packs have no whitelist entries or male-name config in seed.py (they fall through to raw genre check).

## Solution

Move genre-specific metadata from `seed.py` into manifest-level fields on `PackManifest`. Add one new field: `use_male_only_names: bool = false` for male NPC name pool control. seed.py reads this exclusively from the loaded manifest — zero hardcoded fallbacks. All six default packs get fully populated manifest configs in this plan. Delete `_GENRE_TAG_WHITELIST`, `_HISTORICAL_COMBAT`, and `_normalize_genre_key()` entirely. Genre tag whitelists are dropped — pools are per-pack via scenario.yaml, selection only draws from current pack's own pool lists, zero cross-pollination risk.

## Firm decisions

1. **Config lives in manifest, not scenario** — `genre_tag_whitelist` and `use_male_only_names` go on PackManifest because they're genre-level metadata (affect name pool generation + validation), not game-start-specific data
2. **Backward compat via empty-default fallbacks** — seed.py checks manifest field first; if empty/false, falls back to current hardcoded behavior for existing packs that haven't been updated yet
3. **Pool entries stay in scenario.yaml** — situation_archetypes, arc_categories, character_dynamics, moral_pressures remain where they are (they're game-start pool data)
4. **No new Pydantic models needed** — just two fields on existing PackManifest class
5. **Space-western uses mixed names by default** — manifest will have `use_male_only_names: false` or omit the field entirely

## Non-goals

- Converting eval packs (static seed_state.yaml format) to pool system
- Updating generate_pack prompts to emit genre_tag_whitelist / use_male_only_names (future work when dynamic pack generation is adapted)
- Adding tests (tests temporarily removed per AGENTS.md)
- Changing the pool entry structure or pre-selection algorithm

## Risks, Ambiguities, and Blockers

- **generate_pack compatibility**: When generate_pack is later updated to emit pool data via ScenarioBrief, it will also need to set manifest fields. This plan does not cover that change but documents what would need updating.
- **Existing pack updates required for full benefit**: The backward-compat fallback means existing packs (zombie-survival, golden-piracy, noir-1930s) continue working via hardcoded whitelists until their manifest.yaml files are updated with `genre_tag_whitelist` entries. This is acceptable — the goal is to enable new pack authoring without hardcoded lists.
- **_HISTORICAL_COMBAT fallback**: Packs not yet migrated (space-western, sengoku-japan, allied-ww2) will use manifest field if set; otherwise seed.py falls back to checking genre against `_HISTORICAL_COMBAT` for male name pool selection during transition period.

## Implementation — Phase 1: Manifest schema additions + pack.yaml updates

### Context files to load
- `ccya/pack.py` (full file)
- All six manifest files in `packs/default/*/pack.yaml`

### Detailed steps

#### Step 1.0 — Add two fields to PackManifest model

**File:** `ccya/pack.py`, class PackManifest (after existing fields, around line 231)

**What:** Add two new optional fields:
- `genre_tag_whitelist: list[str] = Field(default_factory=list)` — allowed tag substrings for pool entry validation per genre. Each pack must populate this with its full vocabulary.
- `use_male_only_names: bool = False` — when true, male-only name pools are used for NPC/PC generation regardless of genre check

**Why:** These fields move genre-specific metadata out of hardcoded Python sets into pack-declared manifest data. Each pack explicitly declares its vocabulary and naming rules alongside other pack metadata (genre, tone_tags, baseline_facts). All packs get fully populated in this plan — zero fallbacks needed.

#### Step 1.1 — Update manifest files for all six packs

**Files:** All `packs/default/*/pack.yaml` (zombie-survival, golden-piracy, noir-1930s, space-western, sengoku-japan, allied-ww2)

**What:** Add manifest fields to each pack:
- zombie-survival/pack.yaml — add `genre_tag_whitelist` with all 40+ tags from current whitelist["zombie"]; set `use_male_only_names: false` (not in _HISTORICAL_COMBAT)
- golden-piracy/pack.yaml — add `genre_tag_whitelist` with pirate whitelist tags; add `use_male_only_names: true`
- noir-1930s/pack.yaml — add `genre_tag_whitelist` with noir whitelist tags; add `use_male_only_names: true` (currently relies on _HISTORICAL_COMBAT check)
- space-western/pack.yaml — set `use_male_only_names: false`; populate genre_tag_whitelist with frontier/rebel/scrap-tech vocabulary tags
- sengoku-japan/pack.yaml — add `use_male_only_names: true` (currently via _HISTORICAL_COMCAT); populate genre_tag_whitelist with feudal/warrior/honor vocabulary tags
- allied-ww2/pack.yaml — add `use_male_only_names: true` (currently via _HISTORICAL_COMCAT); populate genre_tag_whitelist with military/war/gritty vocabulary tags

**Why:** All six packs get fully populated manifest fields — zero fallbacks. seed.py will read exclusively from manifest after Phase 2 removes all hardcoded constants.

**Validation:** `python -c "from ccya.pack import load_pack; p = load_pack('zombie-survival'); print(p.manifest.genre_tag_whitelist[:3])"` should show first 3 whitelist tags from manifest.

### Tests to write or update
None (tests temporarily removed per AGENTS.md).

### REPOMAP updates required
- `ccya/pack.py` — add genre_tag_whitelist and use_male_only_names fields to PackManifest class
- `packs/default/zombie-survival/pack.yaml` — add genre_tag_whitelist list
- `packs/default/golden-piracy/pack.yaml` — add genre_tag_whitelist + use_male_only_names: true

## Implementation — Phase 2: seed.py refactor to read manifest config

### Context files to load
- `ccya/engine/seed.py` (full file)
- `ccya/pack.py` (Phase 1 changes only)

### Detailed steps

#### Step 2.0 — Refactor _validate_genre_sanity to use manifest whitelist

**File:** `ccya/engine/seed.py`, function `_validate_genre_sanity()` (lines 120-137), and its callers in `_preselect_pools()` (line 186) + fallback loop (line 199)

**What:** Change the signature from `_validate_genre_sanity(selected, genre)` to accept manifest whitelist:
```python
def _validate_genre_sanity(selected: dict[str, Any], whitelist: list[str]) -> bool:
    """Validate that selected entry has at least one tag matching the whitelist."""
    if not whitelist:
        return True  # empty whitelist = no validation (pack authoring phase)
    tag = selected.get("id", "") + " " + " ".join(selected.get("tags", []))
    for substring in whitelist:
        if substring.lower() in tag.lower():
            return True
    _log.warning(
        "Genre sanity check failed — entry has no matching genre tags. id=%s tags=%s",
        selected.get("id"),
        selected.get("tags"),
    )
    return False
```

Then update `_preselect_pools()` to receive manifest whitelist as parameter and pass it through instead of using `_GENRE_TAG_WHITELIST`. The fallback re-selection loop also passes the same whitelist.

**Why:** Removes dependency on hardcoded genre whitelist dict from seed.py. Each pack now declares its own vocabulary via manifest, making new genres possible without code changes to seed.py. Empty whitelist = no validation (during authoring phase before pools are populated).

#### Step 2.1 — Refactor male name pool check to use manifest flag only

**File:** `ccya/engine/seed.py`, `_build_generate_seed_messages()` function, lines 219-230

**What:** Replace the inline `_HISTORICAL_COMBAT` set with manifest-driven logic:
```python
use_male = pack.manifest.use_male_only_names
male_npc_pool = generate_npc_names(locales, count=10, gender="male") if use_male else None
```

Delete `_HISTORICAL_COMCAT` entirely — zero fallbacks. All packs have manifest fields set in Phase 1 + Phases 3-5.

**Why:** Each pack explicitly opts into male-only naming via manifest field. space-western has `use_male_only_names: false`, sengoku-japan/allied-ww2/noir/pirate have it set to true.

#### Step 2.2 — Remove `_normalize_genre_key()` function

**File:** `ccya/engine/seed.py`, lines 155-163

**What:** Delete the entire `_normalize_genre_key()` function and remove its usage from `_preselect_pools()`. The genre string is now passed directly to manifest whitelist lookup — no normalization needed since each pack declares its own whitelist.

Update `_preselect_pools()` signature to accept `manifest` instead of `genre_str`:
```python
def _preselect_pools(scenario: Any, name_seed: int, manifest: PackManifest) -> dict[str, Any]:
    whitelist = manifest.genre_tag_whitelist or []  # empty during authoring phase
    ...
```

**Why:** `_normalize_genre_key()` was a mapping layer between pack genre strings and hardcoded whitelist keys. With per-pack whitelists in manifest, this indirection is unnecessary — each pack's manifest already identifies it via `id` field, and the whitelist comes directly from that manifest entry.

#### Step 2.3 — Update `_preselect_pools()` callers to pass manifest

**File:** `ccya/engine/seed.py`, line 237 where `_preselect_pools(scenario, name_seed, genre)` is called

**What:** Change call site to:
```python
pool_selection = _preselect_pools(scenario, name_seed, pack.manifest)
```

Also update the fallback re-selection loop inside `_preselect_pools()` to use manifest whitelist instead of genre-based lookup.

#### Step 2.4 — Delete `_GENRE_TAG_WHITELIST` constant entirely

**File:** `ccya/engine/seed.py`, lines 71-103

**What:** Delete the entire `_GENRE_TAG_WHITELIST` dict (lines 69-103). Zero fallbacks needed — all packs have manifest.genre_tag_whitelist populated in Phase 1 + Phases 3-5.

### Tests to write or update
None (tests temporarily removed per AGENTS.md).

### REPOMAP updates required
- `ccya/engine/seed.py` — refactor _validate_genre_sanity to accept whitelist param; remove _normalize_genre_key(); update male name check to manifest-driven with fallback; update _preselect_pools signature and callers

## Implementation — Phase 3: Populate space-western pack pools + strip old inspiration

### Context files to load
- `packs/default/space-western/scenario.yaml` (full file)
- `ccya/prompts/generate_seed_system.j2` (Phase 1 changes only for context)
- `ccya/prompts/generate_seed_user.j2` (Phase 1 changes only for context)

### Detailed steps

#### Step 3.0 — Add genre_tag_whitelist to space-western manifest + strip old inspiration fields

**Files:** 
- `packs/default/space-western/pack.yaml` — add `genre_tag_whitelist:` with frontier/rebel/scrap-tech tags
- `packs/default/space-western/scenario.yaml` — remove entire `opening_situation` section; keep pc, npcs, inventory prose guidance (strip role-specific examples like "deputy", "pilot", "rancher" from pc and inventory)

**Why:** Cleans up old-style inspiration format that causes LLM convergence. The manifest whitelist enables pool entry validation for new genre vocabulary.

#### Step 3.1 — Populate space-western situation_archetypes (10+ entries)

**File:** `packs/default/space-western/scenario.yaml`

**What:** Add `situation_archetypes:` list with ~12 archetypes covering frontier opening moments:
- freighter_under_attack, settlement_siege, dust_storm_chase, mining_town_firefight, crash_landing, supply_interdiction, border_clash, saloon_standoff, convoy_ambush, outpost_defense, customs_inspection, desert_crossing

Each entry gets id + tags (e.g., `tags: [frontier, violence, immediate_action]`). No incompatible_with needed for situations.

#### Step 3.2 — Populate space-western arc_categories (15+ entries)

**File:** Same as Step 3.1

**What:** Add `arc_categories:` list with ~15 categories covering frontier narrative pressures:
- rebellion_vs_authority, settlement_survival, supply_line_warfare, coalition_occupation_resistance, terraforming_crisis, companion_guild_politics, browncoat_legacy, independent_trade_routes, frontier_justice, resource_extraction_conflict, colony_abandonment, rustbelt_decline, militia_assembly, partisan_operations, corporate_land_grab

#### Step 3.3 — Populate space-western character_dynamics (8+ entries with incompatible_with)

**File:** Same as Step 3.1

**What:** Add `character_dynamics:` list with ~8 dynamics covering frontier social positions:
- rim_veteran, coalition_deserter, independent_pilot, town_deputy, companion_registrant, rustbelt_scavenger, displaced_officer, free_trader

Define incompatible pairs (e.g., coalition_deserter incompatible with loyalist — both describe relationship to authority).

#### Step 3.4 — Populate space-western moral_pressures (6+ entries)

**File:** Same as Step 3.1

**What:** Add `moral_pressures:` list with ~6 pressures:
- freedom_vs_security, loyalty_to_rim, independence_isolation, frontier_code, survival_vs_principles, old_loyalties_new_world

#### Step 3.5 — Delete extract_examples.yaml for space-western

**File:** `packs/default/space-western/extract_examples.yaml` (delete entire file)
Also remove the `extract_examples: extract_examples.yaml` line from pack.yaml.

### Tests to write or update
None (tests temporarily removed per AGENTS.md).

### REPOMAP updates required
- `packs/default/space-western/pack.yaml` — add genre_tag_whitelist + use_male_only_names: false; remove extract_examples reference
- `packs/default/space-western/scenario.yaml` — remove opening_situation + arcs prose fields; strip role-specific examples from pc/npcs/inventory inspiration; add all four pool lists

## Implementation — Phase 4: Populate sengoku-japan pack pools + strip old inspiration

### Context files to load
- `packs/default/sengoku-japan/scenario.yaml` (full file)
- `ccya/pack.py` (Phase 1 changes only for manifest fields context)

### Detailed steps

#### Step 4.0 — Add manifest config + strip old inspiration

**Files:**
- `packs/default/sengoku-japan/pack.yaml` — add `use_male_only_names: true`; genre_tag_whitelist empty during transition (to be populated with feudal/warrior/honor tags)
- `packs/default/sengoku-japan/scenario.yaml` — remove opening_situation + arcs prose fields; strip male-name directives from npcs section (keep general NPC quality guidance); keep pc, inventory prose

#### Step 4.1 — Populate sengoku-japan situation_archetypes (~12 entries)

**File:** `packs/default/sengoku-japan/scenario.yaml`

Archetypes: castle_siege, battlefield_ambush, night_raid, honor_duel, mountain_escape, supply_line_attack, village_defense, spy_discovery, traitor_reveal, border_skirmish, retreat_under_fire, assassination_attempt

#### Step 4.2 — Populate sengoku-japan arc_categories (~15 entries)

Archetypes: loyalty_vs_survival, clan_politics, daimyo_succession, war_exhaustion, honor_code_breakdown, vassal_defection, enemy_infiltration, territory_negotiation, battlefield_command, siege_resistance, rebellion_against_lord, peace_undertones, weapon_tech_evolution, supply_crisis, bushido_vs_pragmatism

#### Step 4.3 — Populate sengoku-japan character_dynamics (~8 entries with incompatible_with)

Dynamics: loyal_vassal, ronin_without_master, ashigaru_rising_through_merit, shinobi_spy, temple_warrior, daimyo_heir, defected_commander, peasant_leader

#### Step 4.4 — Populate sengoku-japan moral_pressures (~6 entries)

Pressures: honor_vs_survival, loyalty_to_lord, duty_to_people, cost_of_victory, bushido_idealism, peace_through_warfare

#### Step 4.5 — Delete extract_examples.yaml for sengoku-japan

**File:** `packs/default/sengoku-japan/extract_examples.yaml` (delete entire file)
Also remove the `extract_examples: extract_examples.yaml` line from pack.yaml.

### Tests to write or update
None (tests temporarily removed per AGENTS.md).

### REPOMAP updates required
- `packs/default/sengoku-japan/pack.yaml` — add use_male_only_names: true; genre_tag_whitelist with feudal tags; remove extract_examples reference
- `packs/default/sengoku-japan/scenario.yaml` — remove opening_situation + arcs prose fields; strip male-name directives from npcs; add all four pool lists

## Implementation — Phase 5: Populate allied-ww2 pack pools + strip old inspiration

### Context files to load
- `packs/default/allied-ww2/scenario.yaml` (full file)
- `ccya/pack.py` (Phase 1 changes only for manifest fields context)

### Detailed steps

#### Step 5.0 — Add manifest config + strip old inspiration

**Files:**
- `packs/default/allied-ww2/pack.yaml` — add `use_male_only_names: true`; genre_tag_whitelist empty during transition (to be populated with military/war/gritty tags)
- `packs/default/allied-ww2/scenario.yaml` — remove opening_situation + arcs prose fields; strip male-name directives from npcs section (keep general NPC quality guidance); keep pc, inventory prose

#### Step 5.1 — Populate allied-ww2 situation_archetypes (~12 entries)

Archetypes: firefight_starting_unexpected, retreat_through_burning_village, trench_overrun, beachhead_under_fire, night_ambush, supply_convoy_attack, artillery_preparation, bridge_defense, reconnaissance_in_depth, paratrooper_drop_zone, naval_support_call, medical_evacuation_under_fire

#### Step 5.2 — Populate allied-ww2 arc_categories (~15 entries)

Archetypes: squad_survival, mission_vs_casualties, following_orders_moral_dilemma, enemy_dehumanization, home_front_connection, war_crimes_coverage, prisoner_handling, civilian_collateral, logistics_breakdown, command_incompetence, brotherhood_bonds, fear_management, desertion_stigma, propaganda_vs_reality, post_war_uncertainty

#### Step 5.3 — Populate allied-ww2 character_dynamics (~8 entries with incompatible_with)

Dynamics: rank_and_file_rifleman, radioman_behind_lines, combat_medic, tank_crew_member, scout_reconnaissance, clerk_administrative, veteran_noncommissioned_officer, replacement_conscript

#### Step 5.4 — Populate allied-ww2 moral_pressures (~6 entries)

Pressures: survival_vs_duty, following_orders_vs_conscience, protecting_squad_mates, war_dehumanization, home_front_expectations, ending_the_war_at_any_cost

#### Step 5.5 — Delete extract_examples.yaml for allied-ww2

**File:** `packs/default/allied-ww2/extract_examples.yaml` (delete entire file)
Also remove the `extract_examples: extract_examples.yaml` line from pack.yaml.

### Tests to write or update
None (tests temporarily removed per AGENTS.md).

### REPOMAP updates required
- `packs/default/allied-ww2/pack.yaml` — add use_male_only_names: true; genre_tag_whitelist with military tags; remove extract_examples reference
- `packs/default/allied-ww2/scenario.yaml` — remove opening_situation + arcs prose fields; strip male-name directives from npcs; add all four pool lists
