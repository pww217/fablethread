# World Seed and Character Creation Prompts

## Status
`open`

## Part of
standalone

## Dependencies
- none

## Objective
Two character creation failures that produce broken game state before turn 1: (1) the world generation seed assigns NPC roles that contradict the world pack's tone, genre, and lore — female soldiers are generated for a setting where this is anachronistic, guards are assigned modern-sounding names, factions are inconsistently named — because the seed prompt has no explicit instruction to match NPC role/gender/occupation to the world pack's cultural and demographic guidance; (2) the character creator caps NPC generation at 2 regardless of how many the player requests, because `generate_seed_system.j2` line 99 says "Exactly 2 NPCs" and the `npc_count_override` variable is passed in the Jinja context but never rendered into the user prompt. Neither is a turn-engine issue — both are seed generation prompt problems.

## Non-goals
- Does not change NPC pronoun handling in the turn engine (that works correctly per user feedback).
- Does not add a gender field to NPC Pydantic models.
- Does not change the turn engine's NPC tracking or compendium logic.
- Does not affect `present_npcs` or scene extraction.
- Does not add new fields to `ScenarioBrief` or `PackManifest` Pydantic models.

## Affected files
| File | Change type | Summary of change |
|---|---|---|
| `ccya/prompts/generate_seed_system.j2` | modify | Replace "Exactly 2 NPCs" with configurable count; add NPC role alignment rule |
| `ccya/prompts/generate_seed_user.j2` | modify | Render `npc_count_override` and pass world pack cultural context from `scenario` fields |
| `ccya/engine/seed.py` | modify | Pass `min_named_npcs` from `scenario.constraints` as default when `npc_count_override` is 0 |
| `docs/REPOMAP/prompts.md` | update | Document NPC alignment rule, count rule, and `npc_count_override` rendering |

## Firm decisions

1. NPC role/occupation must match the world pack's cultural and demographic guidance. The seed prompt must receive the relevant world pack fields (factions, name_locales, world_facts, narrator_rules) and include an explicit rule: "Generate NPC roles, occupations, and gender distributions consistent with the world pack's cultural context provided below."
2. The NPC count the player requests in character creation is honored. When `npc_count_override` is 0, fall back to `scenario.constraints.min_named_npcs` (default 2). When `npc_count_override > 0`, use that value. No arbitrary hard cap is imposed beyond what the model can reasonably produce.
3. The truncation is model-side, not parser-side. `generate_seed_system.j2` line 99 says "Exactly 2 NPCs" — this is the hard cap. The parser (`SeedEnvelope` / `SeedScene.present_npcs`) has no truncation logic. Fix is in the prompt, not the parser.
4. No new Pydantic fields are added to `ScenarioBrief`, `PackManifest`, `Constraints`, or `EngineConfig`. Cultural context is drawn from existing fields: `scenario.factions`, `scenario.name_locales`, `scenario.world_facts`, `scenario.narrator_rules`, `scenario.inspiration`.

## Implementation — Phase 1: World Pack Alignment Rule

### Context files to load
- `ccya/prompts/generate_seed_system.j2`
- `ccya/prompts/generate_seed_user.j2`
- `ccya/engine/seed.py` — `_build_generate_seed_messages()` context dict (lines 81-92)
- `ccya/pack.py` — `ScenarioBrief`, `Constraints`, `Faction`, `PackManifest` models

### Overview
Add an explicit NPC role alignment rule to the seed system prompt. Pass the world pack's cultural fields (factions, name_locales, world_facts, narrator_rules) to the seed user prompt so the model has the context it needs.

### Detailed steps

#### Step 1.1 — Add NPC role alignment rule to generate_seed_system.j2

**File:** `ccya/prompts/generate_seed_system.j2`

**What:** Add the following rule after the existing "## Name selection" section (around line 14) and before "## Hard constraints":

```jinja2
## NPC role alignment
{% if scenario and scenario.factions %}
**NPC ROLE ALIGNMENT RULE (MANDATORY):** All generated NPCs must have roles, occupations, titles, and implied demographics consistent with the world pack's cultural and historical context provided below. Specifically:
- Do not assign occupations that are anachronistic or culturally inconsistent with the world pack period.
- Use the name_locales provided in the user prompt to select culturally appropriate names.
- Cross-reference the factions provided below: NPCs affiliated with a faction must have a role consistent with that faction's description.
- If the narrator_rules include tone or cultural guidance, apply it to NPC role assignment.
{% endif %}
```

**Why:** Without this rule, the model draws on its general world knowledge to fill gaps, producing modern-feeling or anachronistic NPCs that break immersion before the game starts. The rule is conditional on `scenario.factions` being present so it doesn't produce empty sections for legacy packs.

**Validation:** Generate a seed with a world pack that specifies factions and narrator_rules. Confirm NPCs have roles consistent with faction descriptions.

***

#### Step 1.2 — Pass world pack cultural fields to generate_seed_user.j2

**File:** `ccya/prompts/generate_seed_user.j2`

**What:** Add a `## npc_generation_context` block after the `## name_pool` section (after line 51) and before `## Output discipline`:

```jinja2
{% if scenario and scenario.factions %}
## npc_generation_context
Factions (use these for NPC role assignment):
{% for f in scenario.factions %}- {{ f.name }} ({{ f.disposition }}): {{ f.description }}
{% endfor %}
{% if scenario.narrator_rules %}Tone/cultural guidance:
{% for rule in scenario.narrator_rules %}- {{ rule }}
{% endfor %}{% endif %}
{% if scenario.world_facts %}World facts (inform NPC roles):
{% for fact in scenario.world_facts %}- {{ fact }}
{% endfor %}{% endif %}
{% endif %}
```

**Why:** The model cannot apply the alignment rule without seeing the world pack's relevant fields. The existing seed prompt passes faction data in `## factions` but the NPC generation section doesn't reference it. This new block explicitly ties faction data to NPC role assignment.

**Validation:** Render `generate_seed_user.j2` with a scenario that has factions. Confirm the `npc_generation_context` block renders with faction names, dispositions, descriptions, and any narrator_rules/world_facts.

***

## Implementation — Phase 2: NPC Count Fix

### Context files to load
- `ccya/prompts/generate_seed_system.j2` — line 99-100: `present_npcs` section says "Exactly 2 NPCs"
- `ccya/engine/seed.py` — `_build_generate_seed_messages()` lines 81-92: context dict
- `ccya/pack.py` — `Constraints.min_named_npcs` (default 2), `PlayerOverrides.npc_count` (default 0)

### Overview
The NPC count truncation is entirely model-side, caused by `generate_seed_system.j2` line 99 saying "Exactly 2 NPCs". The `npc_count_override` variable is already passed in the Jinja context (seed.py line 84-86) but never rendered into the user prompt. The fix: (1) make the system prompt's "Exactly 2" into a variable, (2) render `npc_count_override` in the user prompt, (3) pass `min_named_npcs` as the fallback default.

### Detailed steps

#### Step 2.1 — Make present_npcs count configurable in generate_seed_system.j2

**File:** `ccya/prompts/generate_seed_system.j2`

**What:** Replace line 99-100:
```
## present_npcs
Exactly 2 NPCs that appear in the opening scene — {id: snake_case, name, title, notes: current attitude/situation, bio: durable identity}. These are the characters the player meets immediately.
```

With:
```jinja2
## present_npcs
{% if npc_count_override and npc_count_override > 0 %}
Exactly {{ npc_count_override }} NPCs that appear in the opening scene — {id: snake_case, name, title, notes: current attitude/situation, bio: durable identity}. These are the characters the player meets immediately.
{% else %}
Exactly 2 NPCs that appear in the opening scene — {id: snake_case, name, title, notes: current attitude/situation, bio: durable identity}. These are the characters the player meets immediately.
{% endif %}
```

**Why:** The system prompt's "Exactly 2" is the hard cap the model follows. Making it variable allows the player's request to propagate through.

**Validation:** Render `generate_seed_system.j2` with `npc_count_override=3`. Confirm the rendered text says "Exactly 3 NPCs". Render with `npc_count_override=0`. Confirm it says "Exactly 2 NPCs".

***

#### Step 2.2 — Render npc_count_override in generate_seed_user.j2

**File:** `ccya/prompts/generate_seed_user.j2`

**What:** Add a `## npc_count` block after the `## name_pool` section (after line 51) and before `## Output discipline`:

```jinja2
{% if npc_count_override and npc_count_override > 0 %}
## npc_count
The player requested {{ npc_count_override }} NPCs for the opening scene. Generate exactly that many present_npcs entries.
{% endif %}
```

**Why:** The model needs the count in both system and user prompts to reliably honor it. The system prompt sets the structural rule; the user prompt provides the specific number.

**Validation:** Render `generate_seed_user.j2` with `npc_count_override=3`. Confirm the `npc_count` block renders with the correct count. Render with `npc_count_override=0`. Confirm the block is absent.

***

#### Step 2.3 — Pass min_named_npcs as fallback default in seed.py

**File:** `ccya/engine/seed.py`

**What:** In `_build_generate_seed_messages()` (around line 81-92), update the context dict to include `min_named_npcs` as the fallback:

```python
    ctx = {
        "scenario": scenario,
        "overrides": overrides if (overrides and not overrides.is_empty()) else None,
        "npc_count_override": overrides.npc_count
        if (overrides and overrides.npc_count > 0)
        else 0,
        "min_named_npcs": (
            scenario.constraints.min_named_npcs
            if scenario and scenario.constraints
            else 2
        ),
        "name_pool": name_pool,
        "name_seed": name_seed,
        # Legacy fallbacks for old packs without scenario
        "world_text": pack.world_text,
        "style_text": pack.style_text,
    }
```

**Why:** `npc_count_override=0` means "use the pack default". The `min_named_npcs` field from `Constraints` (default 2) is the pack default. This lets the system prompt use `min_named_npcs` as the fallback value instead of hardcoding 2.

**Validation:** Generate a seed with a dynamic pack where `min_named_npcs=4` and no `npc_count` override. Confirm the system prompt renders "Exactly 4 NPCs".

***

### Tests to write or update
- `tests/test_prompts.py`: render `generate_seed_system.j2` with `npc_count_override=3` — confirm "Exactly 3 NPCs" in rendered text.
- `tests/test_prompts.py`: render `generate_seed_system.j2` with `npc_count_override=0` — confirm "Exactly 2 NPCs" in rendered text.
- `tests/test_prompts.py`: render `generate_seed_user.j2` with `npc_count_override=3` — confirm `npc_count` block renders.
- `tests/test_prompts.py`: render `generate_seed_user.j2` with `npc_count_override=0` — confirm `npc_count` block is absent.
- `tests/test_prompts.py`: render `generate_seed_system.j2` with `scenario.factions` — confirm NPC ROLE ALIGNMENT RULE section renders.
- `tests/test_prompts.py`: render `generate_seed_user.j2` with `scenario.factions` — confirm `npc_generation_context` block renders.
- `tests/test_generate_seed.py`: smoke test — generate seed with `PlayerOverrides(npc_count=3)`, confirm `npc_count_override=3` appears in captured LLM messages.

### REPOMAP updates required
- `docs/REPOMAP/prompts.md`: under `generate_seed_system.j2` / `generate_seed_user.j2` — add NPC ROLE ALIGNMENT RULE, present_npcs count variable, `npc_count_override` rendering, `npc_generation_context` block, `min_named_npcs` fallback.

### Risks
1. **Legacy packs without scenario**: The `npc_count_override` and `min_named_npcs` template blocks use `{% if %}` guards so legacy packs (which have no `scenario`) will render the default "Exactly 2 NPCs" and no `npc_count` block. This is correct behavior.
2. **Requesting many NPCs may produce repetitive entries**: The model may struggle with large counts. The `min_named_npcs` default of 2 is conservative; players can request more via the UI.
3. **`npc_count_override` is already in the context**: The variable name `npc_count_override` is already used in `seed.py` line 84. The plan does not rename it — it just adds rendering of the existing variable in the user prompt and uses it in the system prompt template.

## Ambiguities requiring resolution before execution
1. **`npc_count_override` naming**: The variable is already named `npc_count_override` in `seed.py`. The plan keeps this name for consistency. It represents the player's explicit NPC count request (0 = use pack default).
2. **Fallback default**: When `npc_count_override=0`, the system prompt uses `min_named_npcs` from `scenario.constraints` (default 2). This matches the existing `Constraints` model default and is the correct pack-level default.

## TODO.md update
Add under **P2 — Stability / Fidelity**:
```
- [ ] [World Seed and Character Creation Prompts](plans/world-seed-char-creation.md)
```
