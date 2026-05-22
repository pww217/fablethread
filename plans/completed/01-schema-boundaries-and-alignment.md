# 01-schema-boundaries-and-alignment

## Status
`open`

## Phases

3 phases covering schema-template alignment tooling, boundary model definitions (blocks + boundaries), and schema tests for all typed models.

## Issue

Prompt context is assembled as ad-hoc dicts across 4 LLM call sites (`_rules_messages`, `_narrate_messages`, `_extract_scene_messages`, `_extract_progress_messages`). There are no typed boundary objects between the state dict and `template.render()`. This means:
- Fields can be added to templates without corresponding context data (silent Jinja blanks)
- Context fields can exist in builders but never render (dead code, wasted tokens)
- Refactoring a field name requires hunting through multiple builder functions
- No automated check catches schema drift between models and prompts

## Solution

Introduce three things:
1. An AST-based alignment check that parses `.j2` user templates and verifies every variable reference exists on its boundary model (Section 0 of test strategy)
2. Typed block models (`PlayerBlock`, `LocationBlock`, etc.) that assemble themselves from the raw state dict, composed into per-prompt boundary objects
3. Schema tests validating all new boundary/block models accept valid inputs, reject invalid ones, and default correctly

## Firm decisions

1. Block/boundary models go in a new file `ccya/prompts/context.py` — not mixed with existing Pydantic extraction result models in `models.py`. This keeps prompt context types separate from LLM output types.
2. Blocks are read-only data containers (no mutation of state). They accept the raw `state: dict[str, Any]` and produce typed snapshots via `.model_dump()`.
3. The alignment check runs as a pytest test inside `tests/test_alignment.py`, invoked by existing `make check`. No new make targets or CI config needed.
4. Boundary objects are Pydantic models with block model fields (not dict composition). Each boundary has its own class, not a factory function.
5. Existing extraction result models (`ProgressExtractResult`, etc.) are NOT modified in this plan — they get their own schema tests as part of Layer 1 but the definitions stay where they are.

## Non-goals

- Migrating prompt builder functions to use boundary objects (deferred to a future migration plan — not covered by Plans 1 or 2)
- Render tests or smoke tests (Plan 02)
- Modifying existing Pydantic extraction result models
- System prompt alignment checks (only user prompts are data-driven; system prompts contain hardcoded prose rules)
- NPC roster template consolidation into a single include file (template-level change, not schema boundary work — deferred to future migration)

## Risks, Ambiguities, and Blockers

1. **Ambiguity: how to handle Jinja loops.** `{% for item in inventory %}` accesses items inside the list — should alignment check verify `inventory` exists as a field but not try to validate what's accessed per-item? Yes: only top-level variable references count (the root of each dotted path).
2. **Ambiguity: how to handle Jinja filters.** `{% for t in threads | selectattr('active') %}` — the `selectattr` filter accesses `.active` on items inside a list field. Same rule as loops: only verify top-level variable exists (`threads`).
3. **Risk: `_known_characters_for_extract()` and `build_npc_roster()` are shared helpers.** These produce NPC roster data used by multiple prompt builders but with different variants (rich vs minimal). The block model should capture the common base; variant-specific fields can be added per boundary without duplicating the compendium-lookup logic.
4. **Blocker: none.** This plan is self-contained and doesn't depend on any other work being completed first.

## Implementation — Phase 1: AST-based schema-template alignment check

### Context files to load
- `ccya/prompts/extract_progress_user.j2`
- `ccya/prompts/narrate_user.j2`
- `ccya/prompts/rules_user.j2`
- `ccya/prompts/extract_scene_user.j2`
- `ccya/prompts/extract_state_user.j2`
- `ccya/prompts/narrate_system.j2` (only system prompt that injects dynamic data)
- `Makefile`

### Detailed steps

#### Step 1.1 — Create alignment test file

**File:** `tests/test_alignment.py` (new)

**What:** Write a pytest module that defines the TEMPLATE_CONTRACTS mapping and implements AST-based variable extraction from Jinja templates, then compares against boundary model field names. The contract mapping uses placeholder boundary class references for now (they will be defined in Phase 2); this test file should pass as soon as all contracts are wired up at end of Plan 1.

The alignment check logic:
- Use `jinja2.Environment().parse(template_text)` to get AST nodes
- Walk the AST collecting all `jinja2.nodes.Getattr` and `jinja2.nodes.Getitem` node types
- Extract root variable names from dotted paths (e.g., `pc.name.tags` → root is `"pc"`)
- Skip builtins/control flow: loop variables, filter function calls that don't access data (`|join`, `|length`), macro definitions
- For `{% include %}` nodes, resolve the included template and recursively extract its variable roots (includes pass parent context automatically)
- Compare extracted root names against boundary model field names via `model_fields.keys()`

**Why:** This is Section 0 of the test strategy — catches drift at edit time without running any LLM or rendering. Runs as part of `make check`.

**Validation:** Run `pytest tests/test_alignment.py --collect-only` to confirm it collects but doesn't fail yet (contracts will be placeholder). After Phase 2+3 are complete, all contracts should pass alignment checks.

#### Step 1.2 — Add alignment target to Makefile

**File:** `Makefile`

**What:** Extend the existing `make check` target to also run `pytest tests/test_alignment.py`. The exact change depends on what targets currently exist in the Makefile (read it first). If `check` already runs pytest, just ensure test_alignment is included. If not, add a line like:
```
	@echo "Running schema-template alignment check..."
	@python -m pytest tests/test_alignment.py -q
```

**Why:** Alignment check must run as part of the existing gate (`make check`) per AGENTS.md merge discipline. No new make targets or CI config needed.

**Validation:** `make check` should include alignment test output alongside lint/typecheck results.

### Tests to write or update

- `tests/test_alignment.py`:
  - `test_extract_progress_user_alignment()` — asserts all root variables in template exist on ProgressExtractBoundary
  - `test_narrate_user_alignment()` — same for NarratorBoundary  
  - `test_rules_user_alignment()` — same for RulesBoundary
  - `test_scene_extract_user_alignment()` — same for SceneExtractBoundary
  - `test_state_extract_user_alignment()` — same for StateExtractBoundary (note: state extract boundary may be minimal or not needed if template uses few fields)
  - `test_narrate_system_alignment()` — asserts variables in narrate_system.j2 exist on NarratorSystemBoundary

### REPOMAP updates required

- Add entry for `tests/test_alignment.py` under a new "Test suite" section describing the four-layer test strategy (Section 0 + Layers 1-3)
- Document TEMPLATE_CONTRACTS mapping as part of cross-module contracts if it becomes a public-facing data structure

---

## Implementation — Phase 2: Boundary model definitions (blocks + boundaries)

### Context files to load
- `ccya/models.py` (for existing Pydantic patterns, field naming conventions, validator usage)
- `ccya/prompts/extract_progress_user.j2`
- `ccya/prompts/narrate_user.j2`
- `ccya/prompts/rules_user.j2`
- `ccya/prompts/extract_scene_user.j2`
- `ccya/prompts/extract_state_user.j2`
- `ccya/prompts/_arc.j2`, `_inventory.j2`, `_location.j2`, `_npc_roster.j2`, `_npc_roster_extract.j2`, `_world_state.j2` (all section includes)

### Detailed steps

#### Step 2.1 — Create block models in new file

**File:** `ccya/prompts/context.py` (new)

**What:** Define typed block models that assemble themselves from the raw state dict. Each block is a Pydantic BaseModel with class methods or constructors accepting `state: dict[str, Any]`. Fields are read-only snapshots of what the template needs — not full copies of state data.

Block model definitions (field names and types only):

```python
class PlayerBlock(BaseModel):
    name: str
    tagline: str | None = None
    concept: str | None = None
    stats: dict[str, int]  # {strength/dexterity/wits/lore/charisma/resolve: int}
    conditions: list[Condition]

class LocationBlock(BaseModel):
    id: str
    name: str
    description: str | None = None

class InventoryBlock(BaseModel):
    items: list[InventoryItem]  # reuses existing InventoryItem model from models.py

class ArcThreadBlock(BaseModel):
    visible_goal: str
    thematic_question: str
    pc_drive: str
    threads: list[ArcThreadSummary]  # simplified thread view for prompts
    discovered_truths: list[str] = Field(default_factory=list)
    hidden_truths: list[str] = Field(default_factory=list)

class ArcThreadSummary(BaseModel):
    """Simplified arc thread data for prompt rendering (subset of full ArcThread).

    Used by _arc.j2 line 18 and extract_progress_user.j2 line 17. Both templates access: id, scope, urgency, summary, tags, active, last_seen_turn.
    """
    id: str
    summary: str
    scope: Literal["scene", "arc"]
    urgency: Literal["background", "normal", "urgent"]
    tags: list[str] = Field(default_factory=list)
    active: bool
    last_seen_turn: int | None = None  # referenced in _arc.j2 line 18 and extract_progress_user.j2 line 17 as t.last_seen_turn

class WorldStateBlock(BaseModel):
    entries: list[str]  # raw world state strings from scene.world_state[]

class ChronicleEntryBlock(BaseModel):
    """A single chronicle/turn entry for prompt rendering.

    Source: load_recent_chronicle_turns() returns dicts with turn/input/narrative keys (line 94 of state/chronicle.py).
    Templates only use .turn and .narrative — the "input" field is dead in boundary models but preserved from source data shape.
    """
    turn: int
    narrative: str

class PacingBlock(BaseModel):
    directive: str | None = None  # used by extract_progress_user.j2 line 56 and narrate_user.j2 line 82
    beat_hint: str | None = None  # used by narrate_user.j2 lines 84-87 only (not in extract_progress)
    gate: bool | None = None  # used by extract_progress_user.j2 line 57 only (dead field on NarratorBoundary's pacing_context)

class LastSeenBlock(BaseModel):
    """Last-seen metadata for an NPC in the roster."""
    turn: int
    location_id: str
    location_name: str

class NPCRosterEntryBlock(BaseModel):
    """Single entry in an NPC roster for prompt rendering.

    Source shapes vary by origin: build_npc_roster() outputs dicts with last_seen as a dict (turn/location_id/location_name) from compendium data, or None for present/recently_left NPCs. Template extract_scene_user.j2 line 7 accesses n.last_seen.location_name — not a string.
    """
    id: str
    name: str
    title: str | None = None
    bio: str | None = None
    presence: NpcPresence  # reuses existing enum from models.py
    motivation: str | None = None
    fear: str | None = None
    leverage: str | None = None
    notes: str | None = None
    last_seen: LastSeenBlock | None = None

class NPCRosterBlock(BaseModel):
    entries: list[NPCRosterEntryBlock]
```

Each block has a class method `from_state(state)` that extracts and constructs itself from the raw state dict. The implementation reads directly from known keys (e.g., `state["pc"]`, `state["location"]`) without mutation.

**Why:** Blocks are reusable typed building blocks. If you add a field to `PlayerBlock`, every boundary that composes it gets access to that field automatically through type checking of the boundary object's `.model_dump()`. New prompts assemble by composing existing blocks rather than building dicts from scratch.

#### Step 2.2 — Define per-prompt boundary objects

**File:** `ccya/prompts/context.py` (continued)

**What:** Define boundary models that compose block instances as fields. Each boundary corresponds to one user prompt template:

```python
class RulesBoundary(BaseModel):
    """Context for rules_user.j2."""
    pc: PlayerBlock
    location: LocationBlock
    recent_turns: list[ChronicleEntryBlock]  # sliced to last entry
    user_input: str
    meta: dict[str, int]
    present_npcs: list[NPCRosterEntryBlock]
    last_outcome: str | None = None

class NarratorBoundary(BaseModel):
    """Context for narrate_user.j2.

    Source: _narrate_messages() user_ctx (lines 72-104). Note that _location.j2 and _inventory.j2 includes access state.location/state.inventory,
    so these are NOT separate top-level fields — they're accessed via the `state` dict.
    ArcThreadBlock is exposed as `current_arc` to match _arc.j2's variable name (line 1 of _arc.j2).

    NOTE: _narrate_messages passes chronicle_tail, threat_ages, threat_pressure_at, building_threat_imperative_at in user_ctx
    but narrate_user.j2 never uses them. The alignment check will flag these as dead fields — they should be removed from the boundary model.
    """
    pc: PlayerBlock  # maps to {{ pc.* }} (lines 2-6 of narrate_user.j2)
    current_arc: ArcThreadBlock  # maps to {{ current_arc.* }} in _arc.j2 include (line 13 of narrate_user.j2)
    state: dict[str, Any]  # covers state.location, state.inventory, state.scene.world_state accessed by includes
    npc_roster: NPCRosterBlock  # from build_npc_roster() call on line 98 of _narrate_messages
    pacing_context: PacingBlock | None = None
    recent_turns: list[ChronicleEntryBlock]
    prior_history: list[str] = Field(default_factory=list)
    rules_outcome: "RulesOutcome | None" = None
    user_input: str
    momentum: int = 0
    pending_beat: dict[str, Any] | None = None
    meta: dict[str, int]
    scene: dict[str, Any]
    ages: dict[str, int]
    known_npcs: list[dict[str, Any]]
    present_npcs: list[NPCRosterEntryBlock]
    compendium_bios: list[dict[str, Any]]
    pc_allegiance: str | None = None
    world_factions: list[dict[str, str]]
    world_locations: list[dict[str, str]]
    npc_name_pool: dict[str, list[str]]
    recently_left: list[dict[str, Any]]

    # NOTE: chronicle_tail is passed in user_ctx but never used by narrate_user.j2 — alignment check will flag as dead field.

class SceneExtractBoundary(BaseModel):
    """Context for extract_scene_user.j2.

    Source: _extract_scene_messages() passes pc, location, conditions directly (lines 274-282).
    npc_roster comes from build_npc_roster(present_npcs=extraction_ctx.present_npcs_this_turn, known_npcs=_known_characters_for_extract(state, compact=True), recently_left=[]) — outputs dicts with id/name/title/bio/presence/mfl/notes/last_seen. present_npcs is enriched scene data with id/name/title/bio/notes/presence/last_seen (dicts, not NPCRosterEntryBlock instances at current call site).
    """
    pc: PlayerBlock  # passed directly by _extract_scene_messages line 275
    narration: str
    location: LocationBlock
    conditions: list[Condition]
    npc_roster: NPCRosterBlock  # minimal variant (no motivation/fear/leverage) — actually has mfl from compendium lookup
    present_npcs: list[NPCRosterEntryBlock]
    recent_turns: list[ChronicleEntryBlock]
    turn_no: int

class StateExtractBoundary(BaseModel):
    """Context for extract_state_user.j2.

    Source: _extract_state_messages() passes pc, conditions, inventory, intent, turn_no (lines 308-315).
    Template only uses narration/conditions/inventory/intent/turn_no — pc is passed but never rendered.
    """
    conditions: list[Condition]
    inventory: list[InventoryItem]
    intent: "IntentEnvelope | None" = None
    turn_no: int
    narration: str

class ProgressExtractBoundary(BaseModel):
    """Context for extract_progress_user.j2.

    Source: _extract_progress_messages() passes pc, pc_stats (lines 359-361) but extract_progress_user.j2 never renders them — dead fields.
    npc_roster/location/inventory/conditions come from extraction_ctx (lines 363-366).
    all_threads/recent_events/world_state/intent/pacing_context/recent_turns/turn_no/band/pending_beat are top-level variables used by template.

    NOTE: Template uses `world_state` variable name directly (line 29 of extract_progress_user.j2), NOT world_state_entries.
    ArcThreadBlock's threads are accessed via top-level all_threads (not current_arc).
    """
    narration: str
    npc_roster: NPCRosterBlock  # from extraction_ctx.present_npcs_this_turn + _known_characters_for_extract(compact=True)
    location: LocationBlock
    conditions: list[Condition]
    inventory: list[InventoryItem]
    all_threads: list[ArcThreadSummary]  # source is state.arc.threads (raw dicts) — Pydantic coerces since ArcThreadSummary field names match dict keys; schema tests must validate both raw-dict and object inputs
    world_state: list[str | dict[str, Any]]  # template uses `world_state` variable name (line 29 of extract_progress_user.j2)
    intent: "IntentEnvelope | None" = None
    pacing_context: PacingBlock | None = None
    recent_turns: list[ChronicleEntryBlock]
    turn_no: int
    band: str
    pending_beat: dict[str, Any] | None = None

    # NOTE: _extract_progress_messages passes pc and pc_stats in user_ctx but extract_progress_user.j2 never renders them.
    # The alignment check will flag these as dead fields — they should be removed from the boundary model.

class NarratorSystemBoundary(BaseModel):
    """Context for narrate_system.j2 (only system prompt with dynamic data).

    Source: _narrate_messages() line 106-110 passes pack_style, narrator_rules, world_rules, current_arc.
    Template uses `current_arc` variable name — boundary field must match.
    """
    pack_style: str
    narrator_rules: list[str]
    world_rules: list[str]
    current_arc: ArcThreadBlock  # maps to {{ current_arc.* }} in narrate_system.j2 (same as _arc.j2)
```

**Why:** These are the public boundary objects that get `.model_dump()`-ed and passed to `template.render()`. They enforce schema discipline — no more ad-hoc dicts. The field names match what templates expect (root variable names extracted from Jinja AST).

#### Step 2.3 — Wire TEMPLATE_CONTRACTS mapping in alignment test

**File:** `tests/test_alignment.py`

**What:** Replace placeholder boundary class references with the actual boundary classes imported from `ccya.prompts.context`. The mapping:
```python
TEMPLATE_CONTRACTS = {
    "extract_progress_user.j2": ProgressExtractBoundary,
    "narrate_user.j2": NarratorBoundary,
    "rules_user.j2": RulesBoundary,
    "extract_scene_user.j2": SceneExtractBoundary,
    "extract_state_user.j2": StateExtractBoundary,  # if defined; may be minimal
    "narrate_system.j2": NarratorSystemBoundary,
}
```

**Why:** This wires up the alignment check so it can actually validate against real boundary models. After this step, `make check` will fail on any template that references a variable not present on its boundary model (and warn about dead fields).

### Tests to write or update

- Boundary block/boundary schema tests go in Phase 3 of this plan
- Alignment test contracts wired up in Step 2.3 above

### REPOMAP updates required

- Add entry for `ccya/prompts/context.py` under a new "Prompt context types" section describing the block+boundary model pattern
- Update existing entries that mention ad-hoc dict assembly to reference boundary objects as the target state

---

## Implementation — Phase 3: Schema tests for all typed models

### Context files to load
- `ccya/prompts/context.py` (block and boundary definitions from Phase 2)
- `ccya/models.py` (existing extraction result model definitions)
- Existing constants referenced in eval framework (`ccya/eval/engine_mirror.py`)

### Detailed steps

#### Step 3.1 — Create schema test file for block/boundary models

**File:** `tests/test_schema.py` (new)

**What:** Pytest module with tests validating boundary and block model behavior:
- **Valid input acceptance**: Construct each boundary/block from realistic synthetic state data, assert `.model_dump()` produces correct dict structure
- **Invalid input rejection**: Pass malformed data to constructors, assert validation errors are raised (wrong types, missing required fields)
- **Default values**: Test that optional fields default correctly when not provided in state

Test functions:
```python
def test_player_block_accepts_valid_state()
def test_player_block_rejects_missing_name()
def test_location_block_defaults_description_to_none()
def test_narrator_boundary_model_dump_produces_template_context()
def test_progress_extract_boundary_includes_post_delta_inventory()
# ... one per boundary + block combination

def test_npc_roster_rich_variant_includes_motivation_fear_leverage()
def test_npc_roster_minimal_variant_excludes_mfl_fields()
```

**Why:** Layer 1 of the test strategy — validates typed boundary models accept valid inputs, reject invalid ones, and default correctly. Fast, no I/O, no templates. Catches schema drift at definition time.

#### Step 3.2 — Create schema tests for existing extraction result models

**File:** `tests/test_schema.py` (continued)

**What:** Add tests validating the existing Pydantic extraction result models (`ProgressExtractResult`, `SceneExtractResult`, `StateExtractResult`) that are part of the prompt-out boundary:
- **Valid input acceptance**: Construct from realistic LLM-like JSON data, assert model validates correctly
- **Invalid input rejection**: Pass malformed extractions (wrong types for required fields)
- **Coercion validators work**: Test `_coerce_*` field validators handle string→dict coercion as expected
- **Model config behavior**: Verify `model_config = {"extra": "ignore"}` on StateExtractResult silently drops unknown keys

Test functions:
```python
def test_progress_extract_result_accepts_valid_json()
def test_scene_extract_result_coerces_npc_remove_strings_to_dicts()
def test_state_extract_result_ignores_extra_fields_from_llm()
def test_gm_beat_nullifies_instruction_under_40_chars()
# ... covering all existing extraction result models and their validators

def test_momentum_clamped_to_range()  # behavioral invariant from old suite
def test_pc_conditions_cap_at_five_fifo_eviction()
```

**Why:** These are the prompt-out boundary contracts — data coming back FROM LLMs INTO Python. They must be validated at the boundary, not buried inside extraction pipeline logic. Preserving key invariants from the deleted test suite (momentum clamping, condition cap, GM beat validation).

#### Step 3.3 — Run full make check to verify all phases pass together

**What:** After Phases 1-3 are complete, run `make check` end-to-end:
```bash
make check
```

This should include: lint (ruff), typecheck (mypy), alignment tests, and schema tests. All must pass before proceeding to Plan 2 (render/smoke tests).

**Why:** Final gate verification per AGENTS.md merge discipline. Confirms all three phases of this plan work together without conflicts.

### Tests to write or update

- `tests/test_schema.py`:
  - Block model tests: valid input, invalid input rejection, default values for PlayerBlock, LocationBlock, InventoryBlock, ArcThreadBlock, WorldStateBlock, ChronicleEntryBlock, PacingBlock, LastSeenBlock, NPCRosterBlock (rich and minimal variants)
  - Boundary object tests: NarratorBoundary, RulesBoundary, SceneExtractBoundary, ProgressExtractBoundary — valid construction from synthetic state data, `.model_dump()` produces correct dict keys matching template expectations
  - Extraction result model tests: ProgressExtractResult, SceneExtractResult, StateExtractResult — coercion validators, extra field handling, GMBeat instruction quality validation
  - Behavioral invariant tests: momentum clamping [-3,+3], PC conditions cap at 5 FIFO eviction

### REPOMAP updates required

- Update "Test suite" section to reflect the four-layer strategy (Section 0 + Layers 1-3) with file locations and purposes
- Document that `tests/test_schema.py` covers both boundary models AND extraction result model validation
