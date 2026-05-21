# Dynamic Seed Generation — Pool-Based Pre-Selection

## Status
`open`

## Phases

4 phases covering: (1) new Pydantic models for pool entries, (2) Python pre-selection logic in seed.py, (3) prompt template updates with synthesis guidance and context injection, (4) populating all three default packs with actual pool data.

## Issue

Default pack game starts converge on nearly identical opening situations despite being "dynamic." The LLM reads prescriptive scenario menus (e.g., `opening_situation` prose listing specific scenarios like "fix power grid," "boarding action in progress," "murder investigation") as instructions to pick one — and reliably picks the most generic option every time. Temperature (0.9) affects word choice, not structural decisions like which archetype to select. The result: zombie-survival always produces an electrician/mechanic fixing infrastructure with zombies; pirates always produce a boarding action in progress defending; noir always produces investigating a murder related to corrupt unions.

Arcs are equally generic ("fix the water pump") — near-term tasks without escalation paths, stakes (why care?), or follow-up consequences. World state often contains nebulous lore of no gameplay significance rather than hard constraints that affect choices.

## Solution

Replace freeform LLM scenario selection with pre-selected archetype pools. Before generation starts, Python hashes `name_seed` to independently select ONE entry from each of four genre-specific pools (situation_archetype, arc_category, character_dynamic, moral_pressure). Only the selected entry (not a menu of all options) is fed as context into the prompt alongside existing inspiration guidance. The LLM generates freeform specifics (names, events, outcomes) guided by these abstract pattern-level selections rather than prescriptive scenario menus.

With 10+ × 15+ × 8-10 × 6 = ~7,200 combinations per pack, each game start produces a structurally different opening while maintaining genre coherence through tag-based validation and explicit synthesis guidance in the prompt telling the LLM how to weave elements together.

## Firm decisions

1. **Pre-select from named pools before generation** — hash name_seed to pick ONE entry per pool (with incompatible_with conflict resolution), feed only selected item (not a menu of all options)
2. **Four pools:** situation_archetype (10+), arc_category (15+), character_dynamic (8-10), moral_pressure (6+)
3. **Pool entries are abstract patterns** — id + tags, no specific events/names/outcomes
4. **Genre-specific pools per pack** — not shared across packs; tag vocabulary loses meaning if cross-genre
5. **Python validates genre sanity only** — reject/re-roll if selected entry has out-of-genre tags; explicit within-pool incompatible_with conflict resolution (not between pools)
6. **Explicit within-pool incompatibilities** via `incompatible_with: list[str]` field on each pool entry (e.g., trusted_insider incompatible with pariah — both describe social position, can't coexist as character dynamic)
7. **Remove extract_examples.yaml content** across all packs — they encode specific scenario patterns, not just schema format (dead metadata per grep verification: zero Python references to `extract_example`)
8. **Strip inspiration fields to principles only** — remove prescriptive scenario menus from opening_situation (field removed entirely) and pc (keep as general quality guidance, remove role-specific examples like "electrician/mechanic")
9. **Top-down generation order:** arc_category (stakes/why care?) → world_state (permanent pressures) → recent_events (what shifted) → situation_archetype (opening moment) → character_dynamic (PC's position in power structure) → moral_pressure (personal stake/NPCs/world state guidance/thematic_question)
10. **Recent events guided by situation archetype** — freeform but anchored, not completely unconstrained; explicit rule: recent_events cannot contradict arc threads (e.g., can't say someone is dead if an arc thread references them as alive)
11. **World state must support arc pressure** — no "nebulous lore"; each fact should affect gameplay choices (border closures, banned technologies, faction blockades); explicit rule: world_state facts cannot contradict arc_category (e.g., can't say "all factions cooperate peacefully" when arc is power_struggle)
12. **Merge thematic_question with moral_pressure** — one source of truth; moral_pressure.id directly guides the generated question (the LLM writes a one-sentence question capturing the core moral dilemma expressed by that pressure, e.g., survival_vs_humanity → "How much of yourself do you spend to save one life?")

## Non-goals

- Dynamic/custom pack (generate_pack) adaptation — noted as future work, not planned here
- Changes to turn pipeline (narrate.py, extraction, arc advancement during play)
- Changes to static packs (eval-pack, any hand-authored seed_state.yaml packs)
- Adding tests (tests are temporarily removed per AGENTS.md)

## Risks, Ambiguities, and Blockers

- **Pool entry quality:** The success of this system depends entirely on the quality of pool entries written for each pack. Poorly defined archetypes (too vague or too specific) will undermine generation regardless of pre-selection mechanics.
- **Synthesis guidance effectiveness:** The prompt must clearly explain how four independently-selected elements should weave together without artificial connections. If guidance is unclear, the LLM may produce disjointed outputs despite good pool design.
- **generate_pack_system.j2 compatibility:** Dynamic pack generation (generate_pack) produces ScenarioBrief JSON via LLM. Adding new fields to ScenarioBrief means generate_pack prompts must also be updated to include pool data in generated packs — this plan does not cover that change but documents what would need updating.

## Implementation — Phase 1: Pydantic models

### Context files to load
- `ccya/pack.py` (full file)

### Detailed steps

#### Step 1.0 — Audit Inspiration fields

**File:** `ccya/prompts/generate_seed_user.j2`, lines 24-33

**What:** Confirm which inspiration fields are currently rendered into the seed generation prompt (pc, opening_situation, npcs, inventory). This determines what needs updating in Phase 3.

**Why:** Ensure template changes align with actual field usage.

**Validation:** `grep -n "ins\." ccya/prompts/generate_seed_user.j2`

#### Step 1.1 — Add PoolEntry model (shared by all four pool types)

**File:** `ccya/pack.py`, before ScenarioBrief class

**What:** Define a single shared Pydantic BaseModel subclass:

```python
class PoolEntry(BaseModel):
    """Base entry for archetype pools (situation, arc, character, moral)."""
    id: str
    tags: list[str] = Field(default_factory=list)
    incompatible_with: list[str] = Field(default_factory=list)
```

**Why:** All four pool types share identical fields (id + tags). Using a single `PoolEntry` model avoids duplication while keeping semantic clarity through type aliases. The `incompatible_with` field specifies which other ids in the SAME pool conflict (e.g., trusted_insider incompatible with pariah — both describe social position, can't coexist as character dynamic).

**Validation:** Import check passes; verify PoolEntry accepts id + tags fields.

#### Step 1.2 — Add pool fields to ScenarioBrief

**File:** `ccya/pack.py`, class ScenarioBrief (after existing fields)

**What:** Add four new list fields to ScenarioBrief:

```python
situation_archetypes: list[PoolEntry] = Field(default_factory=list, max_length=16)
arc_categories: list[PoolEntry] = Field(default_factory=list, max_length=20)
character_dynamics: list[PoolEntry] = Field(default_factory=list, max_length=12)
moral_pressures: list[PoolEntry] = Field(default_factory=list, max_length=10)
```

**Why:** These fields hold the pool data loaded from scenario.yaml. `max_length` constraints prevent unbounded lists while allowing sufficient variety (16 situations covers 10+ needed; etc.).

**Validation:** Import check passes with remaining fields; verify no code references `inspiration.opening_situation` outside pack.py:
```bash
grep -rn "opening_situation" ccya/ --include="*.py" | grep -v "pack.py"
```

### Tests to write or update

None (tests temporarily removed per AGENTS.md).

### REPOMAP updates required

- `ccya/pack.py` — add PoolEntry model; modify ScenarioBrief fields (add four pool lists, remove opening_situation from Inspiration)

## Implementation — Phase 2: Pre-selection logic in seed.py

### Context files to load
- `ccya/engine/seed.py` (full file)
- `ccya/pack.py` (Phase 1 changes only — PoolEntry model and fields on ScenarioBrief)

### Detailed steps

#### Step 2.0 — Add pre-selection helper functions

**File:** `ccya/engine/seed.py`, before generate_seed() function

**What:** Implement three Python helpers:

- `_select_from_pool(pool_items, seed, field_name)` — hash the integer seed (using modular arithmetic on `hash(item.id) % len(pool_items)`) to select ONE entry from a list. Returns the selected item dict (`.model_dump()`). If the selected entry has `incompatible_with` ids present in other pools' selections (within same pool type), re-select until no conflict. Raises ValueError if pool is empty (with guidance message for pack authoring).

- `_validate_genre_sanity(selected, all_pools, genre)` — validate that no selected entry has tags outside expected genre vocabulary. For each selected entry, check its `tags` list against a module-level genre tag whitelist (dict mapping genre strings to allowed tag prefixes/patterns). If any tag is out-of-genre, return False (triggering re-roll in generate_seed loop).

- `_build_synthesis_context(selected_situation, selected_arc, selected_dynamic, selected_moral)` — build a context dictionary with the four selected entries' ids and tags. This dict is passed to template rendering as `pool_selection`.

**Why:** These functions implement the pre-selection pipeline: hash-based selection from pools (deterministic per name_seed), within-pool incompatibility resolution (re-select if conflicting ids present in same pool type), genre sanity validation (reject/re-roll on out-of-genre picks), and synthesis context building (structured data for prompt injection).

**Validation:** Import check passes; helper functions are pure (no I/O, no side effects) so they can be tested with simple assertions.

#### Step 2.1 — Integrate pre-selection into generate_seed()

**File:** `ccya/engine/seed.py`, function generate_seed(), around lines 163-170 (before message building)

**What:** After validation gate (line 163-164) and before `_build_generate_seed_messages()` call (line 170), insert pre-selection logic:

```python
# Pre-select from archetype pools (deterministic per name_seed, resolve conflicts)
pool_selection = _preselect_pools(scenario, name_seed)
```

Where `_preselect_pools()` calls the three helpers above and returns a dict with keys `situation`, `arc`, `character_dynamic`, `moral_pressure` (each containing id + tags).

**Why:** This is where pre-selection happens — before any prompt context is built, ensuring selected values are available to both message building (Phase 3) and the LLM call.

**Validation:** Import check passes; verify generate_seed still accepts same parameters (no signature change).

#### Step 2.2 — Pass pool_selection into template context

**File:** `ccya/engine/seed.py`, function _build_generate_seed_messages(), ctx dict (around lines 91-108)

**What:** Add `"pool_selection": pool_selection` to the ctx dictionary passed to both Jinja templates.

**Why:** The prompt templates need access to selected pool entries for context injection (Phase 3).

**Validation:** Import check passes; verify ctx dict structure unchanged (just one new key added).

### Tests to write or update

None (tests temporarily removed per AGENTS.md).

### REPOMAP updates required

- `ccya/engine/seed.py` — add _select_from_pool, _validate_genre_sanity, _build_synthesis_context helpers; modify generate_seed() to call pre-selection before message building; modify _build_generate_seed_messages ctx dict

## Implementation — Phase 3: Prompt template updates

### Context files to load
- `ccya/prompts/generate_seed_system.j2` (full file)
- `ccya/prompts/generate_seed_user.j2` (full file, lines 1-72)

### Detailed steps

#### Step 3.0 — Add synthesis guidance section to system prompt

**File:** `ccya/prompts/generate_seed_system.j2`, after existing "Absolute rules" section (after line ~11), before "Name selection" (line ~13)

**What:** Insert a new section:

```markdown
## Seeded context (pre-selected before generation)

The following elements were independently selected from genre pools by the engine. They are NOT a menu — they are four independent narrative dimensions that you must weave into something coherent:

- **SITUATION ARCHETYPE** ({{ pool_selection.situation.id }}): Shapes your opening moment. Let it influence what kind of pressure or tension the player walks into, not specific details.
- **ARC CATEGORY** ({{ pool_selection.arc.id }}): Shapes longer-term narrative direction. The visible_goal should build on this pattern over multiple turns, not resolve in one action. Arc threads must have escalation paths — each thread describes a situation with inherent tension capable of sustaining 5–10 turns, not single events or scripted sequences.
- **CHARACTER DYNAMIC** ({{ pool_selection.character_dynamic.id }}): Shapes who the PC is relative to power structures and other people in this world. Let it influence social positioning, relationships, and what authority/leverage they have (or lack). The PC bio must be consistent with this dynamic (e.g., if trusted_insider, show community ties; if free_agent, show independence).
- **MORAL PRESSURE** ({{ pool_selection.moral_pressure.id }}): Shapes the ethical dilemma driving immediate personal stakes. This DIRECTLY GENERATES your thematic_question — write it as a one-sentence question capturing the core moral tension expressed by this pressure (e.g., survival_vs_humanity → "How much of yourself do you spend to save one life?").

These were chosen independently. Tension between them is expected and desirable. Weave them into something coherent — don't force artificial connections.

## Generation order (generate from wide scope to narrow)

Build your output in this order, using everything already established before generating what comes next:

1. **PC** (bio, stats, tagline): Who the character is
2. **World state** (3 immutable facts): Permanent pressures of the world — must establish forces relevant to arc_category (not nebulous lore; each fact affects gameplay choices like border closures, banned technologies, faction blockades)
3. **Recent events** (immediate pre-story context): What just shifted in this world (days/weeks before opening). Must naturally lead into situation_archetype and cannot contradict arc threads (e.g., can't say someone is dead if an arc thread references them as alive)

4. **Opening scene / NPCs**: Instantiates the situation_archetype concretely — who's present, what they're doing, how character_dynamic shapes their relationship to power structures
5. **Inventory**: Items tied to PC's top skills (existing rule unchanged)

6. **Campaign arc** (visible_goal, thematic_question, hidden_truths, threads): Generate these LAST, informed by EVERYTHING established above — PC bio, world_state pressures, recent_events shifts, situation_archetype opening moment, character_dynamic social positioning, moral_pressure ethical tension:
   - **visible_goal**: Multi-stage objective emerging from ALL prior context (not just arc_category alone). What happens after the first step succeeds? After it fails? Why does someone care enough to keep going when things get hard?
   - **thematic_question**: Directly generated by moral_pressure.id — write a one-sentence question capturing the core moral dilemma (e.g., survival_vs_humanity → "How much of yourself do you spend to save one life?")
   - **hidden_truths**: What the narrator knows that contradicts or deepens what's visible. Align with both arc_category (narrative pressure) and moral_pressure (ethical tension). These are secrets the player must discover through play, not obvious facts.
   - **active_threads** (scope="arc"): Medium-term sustained tensions (5–10 turns capability) building on arc_category, PC bio, world_state pressures, recent_events shifts — longer-term narrative arcs with inherent escalation potential
   - **latent_threads** (scope="scene" or "arc"): Threads that unlock when conditions are met. Scene-level threads emerge from situation_archetype (immediate tensions tied to opening moment). Arc-level latent threads build on arc_category and character_dynamic

Thread quality rules (unchanged from existing):
- Threads must be substantial medium-term goals capable of sustaining 5–10 turns. They represent ongoing narrative arcs, not single events or observations.
- Each thread should describe a situation with inherent tension and stakes — something that naturally escalates over time. Not a static fact.

## Cross-field consistency rules (MANDATORY)

These constraints prevent logical contradictions across generated fields:

1. **recent_events vs arc threads:** recent_events cannot state someone is dead if any arc thread references them as alive (and vice versa). If an arc mentions protecting "Mayor Chen," recent_events can say she's missing or injured but not that she's been found dead.

2. **world_state vs arc_category:** world_state facts must establish pressures consistent with the arc category. Cannot state "all factions cooperate peacefully" when arc is power_struggle. Each of the 3 world_state facts must directly affect gameplay choices (border closures, banned technologies, faction blockades). No nebulous lore — no historical backstory older than one generation unless it's an active constraint right now.

3. **character_dynamic vs PC bio:** character dynamic shapes who the PC is relative to power structures. If trusted_insider, bio must show community ties and authority; if free_agent, bio must show independence from institutions (not embedded connections).

4. **moral_pressure vs thematic_question:** moral_pressure.id directly generates thematic_question — write a one-sentence question capturing the core moral dilemma expressed by that pressure (e.g., survival_vs_humanity → "How much of yourself do you spend to save one life?").
```

**Why:** This is the core synthesis guidance telling the LLM how to combine four independently-selected elements into coherent output. The explicit generation order (wide scope → narrow scope) ensures arc components (visible_goal, hidden_truths, threads) are generated LAST informed by everything established before them — PC bio, world_state pressures, recent_events shifts, situation_archetype opening moment, character_dynamic social positioning, moral_pressure ethical tension. This creates a related universe where all elements feel connected rather than independently assembled. It also enforces arc escalation (multi-stage visible_goal, sustained threads) which addresses the "fix the water pump" problem directly, and adds explicit cross-field consistency rules preventing contradictions between generated fields (recent_events contradicting arc threads, world_state contradicting arc_category).

**Validation:** Template renders without Jinja errors when pool_selection context is provided (verify in Phase 4 with actual data).

#### Step 3.1 — Inject selected pool entries into user prompt

**File:** `ccya/prompts/generate_seed_user.j2`, after existing content (after line ~70, before "## Output discipline")

**What:** Insert a new section between creative_direction and output discipline:

```markdown
## Pool selection (independently chosen — weave them together)

SITUATION ARCHETYPE: {{ pool_selection.situation.id }} (tags: {{ pool_selection.situation.tags | join(", ") }})
ARC CATEGORY: {{ pool_selection.arc.id }} (tags: {{ pool_selection.arc.tags | join(", ") }})
CHARACTER DYNAMIC: {{ pool_selection.character_dynamic.id }} (tags: {{ pool_selection.character_dynamic.tags | join(", ") }})
MORAL PRESSURE: {{ pool_selection.moral_pressure.id }} (tags: {{ pool_selection.moral_pressure.tags | join(", ") }})

These four elements shape your generation. The situation archetype defines the opening moment's pressure type; arc category shapes longer-term narrative direction with escalation potential; character dynamic places the PC within power structures and relationships; moral pressure creates immediate ethical tension that DIRECTLY GENERATES thematic_question (write as a one-sentence question capturing core moral dilemma).

Recent events should naturally lead into the situation archetype — they are days/weeks before the opening, showing what just shifted in this world. World state must establish permanent pressures relevant to arc category (not nebulous lore; each fact should affect gameplay choices like border closures, banned technologies, faction blockades).
```

**Why:** User prompt is where concrete context lives (names, pools, inspiration prose). Injecting selected pool entries here gives the LLM explicit guidance on how recent_events and world_state should relate to the chosen archetypes.

**Validation:** Template renders without Jinja errors when pool_selection context is provided (verify in Phase 4 with actual data).

#### Step 3.2 — Remove opening_situation from user prompt rendering

**File:** `ccya/prompts/generate_seed_user.j2`, lines ~27-29

**What:** Remove the `{% if ins.opening_situation %}### opening_situation...` block (lines 27-29). Keep blocks for pc, npcs, inventory.

**Why:** Opening situation is now driven by situation_archetype pool (injected via Step 3.1). The existing freeform prose field was a prescriptive scenario menu — removing it eliminates convergence cause.

**Validation:** Template still renders correctly with remaining inspiration fields (pc, npcs, inventory only).

### Tests to write or update

None (tests temporarily removed per AGENTS.md).

### REPOMAP updates required

- `ccya/prompts/generate_seed_system.j2` — add "Seeded context" synthesis guidance section + cross-field consistency rules
- `ccya/prompts/generate_seed_user.j2` — inject pool selection context; remove opening_situation rendering block

## Implementation — Phase 4: Populate pack data

### Context files to load
- All three packs' scenario.yaml files (zombie-survival, golden-piracy, noir-1930s)
- `ccya/prompts/generate_seed_system.j2` (Phase 3 changes only)
- `ccya/prompts/generate_seed_user.j2` (Phase 3 changes only)

### Detailed steps

#### Step 4.0 — Strip inspiration fields in all three packs

**Files:** 
- `packs/default/zombie-survival/scenario.yaml`, lines ~29-50 (pc + opening_situation sections)
- `packs/default/golden-piracy/scenario.yaml`, lines ~28-48 (pc + opening_situation sections)  
- `packs/default/noir-1930s/scenario.yaml`, lines ~32-51 (pc + opening_situation sections)

**What:** For each pack's scenario.yaml:
1. Remove the entire `opening_situation` section (zombie lines 41-50, pirate lines 38-48, noir lines 42-51). The YAML key is removed entirely (not just emptied — field no longer exists on Inspiration model per Phase 1).

**Why:** Remove prescriptive scenario menus that cause LLM convergence. Keep `pc`, `npcs`, and `inventory` fields as general quality guidance (strip role-specific examples like "electrician/mechanic" from zombie pc, keep as broad principles about character depth).

**Validation:** YAML files parse correctly with remaining fields; no syntax errors.

#### Step 4.1 — Populate situation_archetypes (all three packs)

**Files:** `packs/default/zombie-survival/scenario.yaml`, `golden-piracy/scenario.yaml`, `noir-1930s/scenario.yaml`

**What:** Add `situation_archetypes:` list as top-level key alongside existing fields. Each entry has id + tags (incompatible_with left empty for situation archetypes — they don't conflict with each other).

Zombie (10 archetypes): infrastructure_failure, social_betrayal, supply_crisis, faction_conflict, discovery, moral_compromise, survival_dilemma, community_fracture, infrastructure_sabotage, resource_rationing

Pirate (12 archetypes): mutiny_in_progress, naval_engagement, port_intrigue, cargo_heist, disease_onboard, storm_disaster, treasure_discovery, crew_conflict, naval_blockade, mutiny_suppression, port_strike, cargo_sabotage

Noir (10 archetypes): murder_investigation, kidnapping, gang_war, corruption_discovery, witness_protection, heist_aftermath, blackmail, political_scandal, media_manipulation, judicial_rigging

**Why:** These define the opening moment pressure types. Each pack gets 10-12 distinct archetypes covering different situation categories within that genre's vocabulary (meeting firm decision spec of 10+).

**Validation:** YAML parses correctly; ids are snake_case (matching Python hash selection); tags align with genre (no cross-genre contamination).

#### Step 4.2 — Populate arc_categories (all three packs)

**Files:** Same as Step 4.1

**What:** Add `arc_categories:` list alongside situation_archetypes. Each entry has id + tags (incompatible_with left empty for arc categories — they don't conflict with each other).

Zombie (15 categories): power_struggle, resource_scarcity, collapse_conspiracy, leadership_challenge, quarantine_breakdown, territory_dispute, outside_threat_escalation, cult_emergence, information_warfare, infrastructure_rebuilding, faction_defection, infection_evolution, settlement_politics, supply_route_control, moral_decay

Pirate (15 categories): leadership_legitimacy, faction_power_struggle, territorial_control, mutiny_escalation, outside_betrayal, colonial_conspiracy, ship_rivalry, pardon_scheme, naval_blockade, cargo_sabotage, disease_quarantine, storm_wreckage, treasure_hunt, crew_defection, slave_trade

Noir (15 categories): organized_crime_power_struggle, institutional_corruption, gang_territory_dispute, political_conspiracy, underworld_betrayal, media_manipulation, judicial_rigging, witness_intimidation, evidence_tampering, political_shakedown, union_infiltration, police_compromise

**Why:** These define longer-term narrative direction with escalation potential. Each pack gets 15 arc categories covering different story pressures that build over multiple turns (not single-task objectives) (meeting firm decision spec of 15+).

**Validation:** YAML parses correctly; ids are snake_case; tags align with genre vocabulary.

#### Step 4.3 — Populate character_dynamics (all three packs, WITH incompatible_with pairs)

**Files:** Same as Steps 4.1-4.2

**What:** Add `character_dynamics:` list alongside existing fields. Each entry has id + tags + incompatible_with (specifying which ids in the SAME pool conflict).

Zombie (8 dynamics):
```yaml
character_dynamics:
  - id: trusted_insider
    tags: [community, leadership, responsibility]
    incompatible_with: [pariah, free_agent]
  - id: reluctant_outsider  
    tags: [marginalized, independent, distrustful]
    incompatible_with: [trusted_insider, disgraced_leader]
  - id: rising_challenger
    tags: [ambitious, disruptive, emerging_power]
    incompatible_with: [established_authority, free_agent]
  - id: disgraced_leader
    tags: [fallen_status, redemption_needed, community_ties]
    incompatible_with: [trusted_insider, free_agent]
  - id: free_agent
    tags: [independent, unaligned, self_reliant]
    incompatible_with: [trusted_insider, loyal_soldier, established_authority]
  - id: pariah
    tags: [outcast, hunted, isolated]
    incompatible_with: [trusted_insider, reluctant_outsider]
  - id: information_broker
    tags: [connected, secretive, leverage_holding]
    incompatible_with: []
  - id: displaced_elite
    tags: [former_status, loss_of_power, adaptation_needed]
    incompatible_with: []

Pirate (8 dynamics):
character_dynamics:
  - id: loyal_crewman
    tags: [crew_loyalty, working_class, ship_identity]
    incompatible_with: [mutinous_officer, free_agent]
  - id: mutinous_officer  
    tags: [ambitious, dissident, leadership_challenge]
    incompatible_with: [loyal_crewman, established_authority]
  - id: reluctant_recruit
    tags: [forced_into_pirate_life, conflicted, inexperienced]
    incompatible_with: [seasoned_veteran, free_agent]
  - id: seasoned_veteran
    tags: [experienced, hardened, respected_by_crew]
    incompatible_with: []
  - id: free_agent (pirate context)
    tags: [independent, unaligned, self_reliant]
    incompatible_with: [loyal_crewman, established_authority]

Noir (8 dynamics):
character_dynamics:
  - id: embedded_investigator
    tags: [institutional_access, insider_knowledge, system_participant]
    incompatible_with: [outsider_with_access, free_agent]
  - id: outsider_with_access  
    tags: [external_perspective, limited_resources, outside_looking_in]
    incompatible_with: [embedded_investigator, compromised_professional]
  - id: compromised_professional (noir context)
    tags: [ethical_corruption, system_participant, moral_erosion]
    incompatible_with: [outsider_with_access, free_agent]

**Why:** These define the PC's social position relative to power structures. Each pack gets 8 dynamics covering different relationship-to-power archetypes (insider/outsider, trusted/marginalized). The `incompatible_with` field prevents contradictory selections (e.g., trusted_insider and pariah both describe extreme social positions that can't coexist as the same character dynamic).

**Validation:** YAML parses correctly; ids are snake_case; tags align with genre vocabulary; incompatible_with pairs are logically consistent (both ids exist in the same pool, both describe mutually exclusive social positions).

#### Step 4.4 — Populate moral_pressures (all three packs)

**Files:** Same as Steps 4.1-4.3

**What:** Add `moral_pressures:` list alongside existing fields. Each entry has id + tags (incompatible_with left empty for moral pressures — they don't conflict with each other).

Zombie (6 pressures): survival_vs_humanity, protect_the_vulnerable, resource_allocation, truth_control, leadership_burden, trust_dynamics

Pirate (6 pressures): crew_loyalty_vs_self_preservation, mutiny_consequences, code_of_honor, power_concentration, freedom_vs_discipline, legitimate_governance

Noir (6 pressures): truth_vs_self_preservation, institutional_corruption, collateral_damage, evidence_vs_justice, professional_ethics, ends_vs_means

**Why:** These define the ethical dilemma driving immediate personal stakes. Each pack gets 6 moral pressures covering different value conflicts within that genre's thematic vocabulary (meeting firm decision spec of 6+).

**Validation:** YAML parses correctly; ids are snake_case; tags align with genre vocabulary.

#### Step 4.5 — Remove extract_examples.yaml content (all three packs)

**Files:**
- `packs/default/zombie-survival/extract_examples.yaml` (24 lines, delete entire file)
- `packs/default/golden-piracy/extract_examples.yaml` (39 lines, delete entire file)
- `packs/default/noir-1930s/extract_examples.yaml` (39 lines, delete entire file)

**What:** Delete the three extract_examples.yaml files. Also remove the `extract_examples: extract_examples.yaml` line from each pack's pack.yaml (zombie-survival/pack.yaml line 16; find equivalent lines in golden-piracy and noir-1930s).

**Why:** These files are dead metadata — grep confirms zero Python references to `extract_example` across the ccya codebase. They encode specific scenario patterns (concrete JSON with named NPCs, inventory IDs, quest updates) that function as menu items for LLM generation rather than schema format reference. Removing them eliminates another source of convergence.

**Validation:** After deletion, verify no pack loading errors:
```bash
python -c "from ccya.pack import load_pack; p = load_pack('zombie-survival'); print(p.manifest.id)"
```

### Tests to write or update

None (tests temporarily removed per AGENTS.md).

### REPOMAP updates required

- `packs/default/zombie-survival/scenario.yaml` — remove opening_situation; add situation_archetypes, arc_categories, character_dynamics (with incompatible_with), moral_pressures lists
- `packs/default/golden-piracy/scenario.yaml` — same changes as zombie (remove opening_situation; add four pool lists with incompatible_where-applicable)
- `packs/default/noir-1930s/scenario.yaml` — same changes as zombie (remove opening_situation; add four pool lists with incompatible_with on character_dynamics only)

## Dynamic/Custom Pack Adaptation (Future Work)

When adapting this system to generate_pack (dynamic/custom pack generation), the following would need updating:

1. **generate_pack_system.j2** (line ~46-53): The output schema's `inspiration` section needs modification — remove `opening_situation`, add four pool fields (`situation_archetypes`, `arc_categories`, `character_dynamics`, `moral_pressures`) with guidance on entry format (id + tags only, abstract patterns).

2. **generate_pack_system.j2** (line ~12): The existing rule "Inspiration fields must describe qualities and failure modes only" already aligns well — pool entries follow the same principle (abstract patterns, not specific events).

3. **generate_pack.py**: No code changes needed for generate_pack itself (it just deserializes LLM JSON into ScenarioBrief via Pydantic). The new fields will be validated automatically by the updated models from Phase 1.

4. **Pool entry guidance in prompt:** The generate_pack system prompt needs explicit instructions on how many entries to generate per pool (matching default pack counts: ~10 situations, ~15 arcs, ~8 dynamics, ~6 moral pressures) and what constitutes a good abstract pattern entry (id naming convention, tag vocabulary).

## To Investigate

### thread_add gating inconsistency (turn.py lines 1295-1301)

The comment says "Handle thread_add as new arc thread (only when gate == 'allow')" but the code does NOT check `_pc.gate`. There is no explicit `if _pc and _pc.gate != "allow"` guard before processing. This means:
- New threads via `thread_add` can fire every turn (no cooldown, no gate enforcement)
- The PacingContext.gate mechanism (block_add/block_escalate/allow set at lines 602-605 based on deescalation score >= 0.5 → block_escalate) may not actually be gating thread_add despite the comment

Additionally: `_PROMOTION_COOLDOWN_TURNS = 3` (line 94) enforces a minimum turn gap between **latent-to-active promotions** of existing threads, but this does NOT apply to adding entirely new threads via `thread_add`.

These are either (a) an incomplete refactor when unified threads[] replaced the active/latent split, or (b) missing guard code. Should verify intent and fix before relying on pacing controls during play.
