# World Seed and Character Creation Prompts

## Status
`open`

## Part of
standalone

## Dependencies
- none

## Objective
Two character creation failures that produce broken game state before turn 1: (1) the world generation seed assigns NPC roles that contradict the world pack's tone, genre, and lore — female soldiers are generated for a setting where this is anachronistic, guards are assigned modern-sounding names, factions are inconsistently named — because the seed prompt has no explicit instruction to match NPC role/gender/occupation to the world pack's cultural and demographic guidance; (2) the character creator caps NPC generation at 2 regardless of how many the player requests, because a hard cap or a truncation in the seed prompt/parser ignores the player's explicit count. Neither is a turn-engine issue — both are seed generation prompt problems.

## Non-goals
- Does not change NPC pronoun handling in the turn engine (that works correctly per user feedback).
- Does not add a gender field to NPC Pydantic models.
- Does not change the turn engine's NPC tracking or compendium logic.
- Does not affect `present_npcs` or scene extraction.

## Affected files
| File | Change type | Summary of change |
|---|---|---|
| `ccya/prompts/seed_system.j2` (or equivalent) | modify | Add world-pack cultural/demographic alignment rule for NPC role/occupation generation |
| `ccya/prompts/seed_system.j2` (or equivalent) | modify | Remove or raise hard NPC count cap; honor player-specified count up to a configurable max |
| `ccya/prompts/seed_user.j2` (or equivalent) | modify | Pass world pack's demographic/cultural guidance as explicit context for NPC generation |
| `docs/REPOMAP/prompts.md` | update | Document new NPC alignment rule and count cap behavior |

## Firm decisions

1. NPC role/occupation must match the world pack's cultural and demographic guidance. The seed prompt must receive the relevant world pack fields (occupation lists, demographic notes, naming conventions) and include an explicit rule: "Generate NPC roles, occupations, and gender distributions consistent with the world pack's cultural context. Do not assign occupations that contradict the world pack's historical or cultural period."
2. The NPC count the player requests in character creation is honored up to `MAX_SEED_NPCS` (configurable, default 6). The seed prompt must include this count explicitly and be instructed to generate exactly that many.
3. If the parser (not the model) is truncating NPCs, the fix is in the parser, not the prompt. The executor must determine whether the truncation is model-side or parser-side before applying a prompt fix vs. a code fix.
4. No gender field is added to the NPC model. The world pack's cultural guidance is the source of truth for appropriate role/gender distributions at seed time.

## Implementation — Phase 1: World Pack Alignment Rule

### Context files to load
- `ccya/prompts/seed_system.j2` (or the seed generation equivalent)
- `ccya/prompts/seed_user.j2` (or equivalent)
- A sample world pack file (e.g., `packs/default/world.yaml` or equivalent) to confirm what demographic/cultural fields exist

### Overview
Add an explicit NPC role alignment rule to the seed system prompt. Pass the world pack's cultural/demographic fields to the seed user prompt so the model has the context it needs.

### Detailed steps

#### Step 1.1 — Add NPC role alignment rule to seed_system.j2

**File:** `ccya/prompts/seed_system.j2` (executor must confirm exact filename)

**What:** Add the following rule to the NPC generation section:

```
**NPC ROLE ALIGNMENT RULE (MANDATORY):** All generated NPCs must have roles, occupations, titles, and implied demographics consistent with the world pack's cultural and historical context provided below. Specifically:
- Do not assign occupations that are anachronistic or culturally inconsistent with the world pack period.
- Use the world pack's provided naming conventions for NPC names.
- If the world pack specifies demographic or occupational constraints (e.g., "military roles are male-dominated in this setting"), apply them. If no constraint is specified, use balanced defaults.
- Cross-reference the world pack's `factions` field: NPCs affiliated with a faction must have a role consistent with that faction's description.
```

**Why:** Without this rule, the model draws on its general world knowledge to fill gaps, producing modern-feeling or anachronistic NPCs that break immersion before the game starts.

**Validation:** Generate a seed with a world pack that specifies a medieval-equivalent setting. Confirm no NPCs have anachronistic roles. Confirm NPC names follow the naming convention section.

***

#### Step 1.2 — Pass world pack cultural fields to seed_user.j2

**File:** `ccya/prompts/seed_user.j2` (executor must confirm exact filename)

**What:** Add a `## world_pack_context` block containing:
- `setting_period` (the world pack's historical/cultural period description)
- `naming_conventions` (if present)
- `demographic_notes` (if present)
- `faction_list` (name + one-line description for each faction)

```
## world_pack_context
Period: {{ world_pack.setting_period }}
{% if world_pack.naming_conventions %}Naming: {{ world_pack.naming_conventions }}{% endif %}
{% if world_pack.demographic_notes %}Demographics: {{ world_pack.demographic_notes }}{% endif %}
Factions:
{% for f in world_pack.factions %}
- {{ f.name }}: {{ f.description }}
{% endfor %}
```

**Why:** The model cannot apply the alignment rule without seeing the world pack's relevant fields. The existing seed prompt passes character creation choices but may not pass world pack cultural context.

**Validation:** Render `seed_user.j2` with a world pack fixture. Confirm the `world_pack_context` block renders with period, naming, demographics, and factions.

***

## Implementation — Phase 2: NPC Count Cap Fix

### Context files to load
- `ccya/prompts/seed_system.j2`
- The seed output parser (wherever the seed model output is parsed into `GameState` at session start — likely in `ccya/engine/session.py` or `ccya/engine/seed.py`)

### Overview
Determine whether the NPC count truncation is a model error (the model generates only 2 despite being asked for 3+) or a parser error (the model generates the correct count but the parser drops entries). Fix the appropriate layer.

### Detailed steps

#### Step 2.1 — Diagnose truncation source

**File:** seed output parser (executor must identify)

**What:** Before making any change, the executor must:
1. Run a seed generation with `requested_npc_count: 3` and log the raw model output.
2. If the raw output contains 3 NPCs → the truncation is in the parser. Fix the parser's list slice or cap.
3. If the raw output contains only 2 NPCs → the truncation is in the model/prompt. Proceed to Step 2.2.

**Validation:** Raw model output has been inspected and truncation source is confirmed.

***

#### Step 2.2 — Fix prompt-side truncation (if model-side)

**File:** `ccya/prompts/seed_system.j2`

**What:** Add an explicit count instruction to the NPC generation section:

```
**NPC COUNT RULE:** Generate exactly {{ requested_npc_count }} named NPCs. Do not generate fewer. If the requested count seems large, generate the full count anyway — do not truncate. Each NPC must have a unique name, role, and bio.
```

Also pass `requested_npc_count` as a variable in `seed_user.j2`:
```
## npc_count_requested
{{ requested_npc_count }}
```

**Why:** Without an explicit count directive, the model defaults to generating 2 NPCs (a common few-shot default). An explicit count in both system and user prompts eliminates ambiguity.

**Validation:** Request 3 NPCs in character creation. Confirm seed output contains exactly 3 NPC entries. Request 1. Confirm exactly 1. Request 6. Confirm exactly 6.

***

#### Step 2.3 — Fix parser-side truncation (if parser-side)

**File:** seed output parser (executor must identify file)

**What:** Find the list comprehension, slice, or cap that limits NPC count. Replace it with the configurable max from `config.yaml`:

```python
# Find: npcs = parsed_npcs[:2]  (or similar hard limit)
# Replace with:
MAX_SEED_NPCS = config.get("max_seed_npcs", 6)
npcs = parsed_npcs[:MAX_SEED_NPCS]
```

Also add `max_seed_npcs: 6` to `config.yaml` if not present.

**Validation:** Parse a seed output with 4 NPC entries. Confirm all 4 are retained in the resulting `GameState.compendium`.

***

### Tests to write or update
- `tests/test_seed.py` or `tests/test_prompts.py`: render `seed_user.j2` with world pack fixture — confirm `world_pack_context` block renders.
- `tests/test_seed.py`: render `seed_system.j2` — confirm NPC ROLE ALIGNMENT RULE and NPC COUNT RULE present.
- `tests/test_seed.py`: parser test — input 4-NPC seed JSON, confirm 4 entries in compendium output (if parser is the truncation source).

### REPOMAP updates required
- `docs/REPOMAP/prompts.md`: under seed system/user prompt entries — add NPC alignment rule, count rule, world pack context block.
- `docs/REPOMAP/engine.md`: if `max_seed_npcs` config key is added, document it.

### Risks
1. **Seed prompt filename unknown** — the REPOMAP may use a different name (e.g., `world_gen_system.j2`, `char_create_system.j2`). Executor must grep for the seed generation prompt before modifying.
2. **World pack fields may not include all context blocks** — if a world pack does not have `naming_conventions` or `demographic_notes`, the template blocks must handle absence gracefully via `{% if %}`. Already handled in the template above.
3. **Requesting 6 NPCs for a small pack may produce repetitive entries** — a configurable max is the right safety valve, but the user's request should be honored up to that max.

## Ambiguities requiring resolution before execution
1. What is the exact filename of the seed/world generation system prompt? Options: A) `seed_system.j2` B) `world_gen_system.j2` C) `char_create_system.j2`. Executor must grep `ccya/prompts/` for the file that generates the initial NPC compendium.
2. Does the seed prompt receive `requested_npc_count` from the character creation flow, or does it receive the raw character creation form input? Executor must confirm how the player's NPC count request is passed into the seed render call.

## TODO.md update
Add under **P2 — Stability / Fidelity**:
```
- [ ] [World Seed and Character Creation Prompts](plans/world-seed-char-creation.md)
```
