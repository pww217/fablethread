# Pack-gen parity: add archetype pools to generated packs

## Status
`completed`

## Phases

5 phases — update generate_pack prompts, add verification step, clean up dead templates.

## Issue

Generated packs' scenario.yaml is missing all 4 archetype pool fields (`situation_archetypes`, `arc_categories`, `character_dynamics`, `moral_pressures`) that default packs have. When `_preselect_pools()` runs during seed generation on a generated pack, it raises ValueError for empty pools and falls back to no pool guidance — so seeded context injection (opening pressure, arc direction, character dynamics, moral tension) is completely absent from games started with generated packs.

Additionally, generate_pack prompt schemas ask for `inspiration.opening_situation` which doesn't exist on the Inspiration Pydantic model or in any default pack scenario.yaml — it's silently dropped by pydantic's `"extra": "ignore"`.

## Solution

Update both generate_pack wb templates to request and produce all 4 archetype pool sections (~10 entries each, matching default packs), remove stale `opening_sitation` from Inspiration schema guidance, add ASCII/Latin name rules to user prompt for consistency, and delete the dead non-wb template files that are never loaded by engine code.

## Firm decisions

1. Generate ~10 archetype entries per pool (40 total) — matches default packs exactly.
2. Pool entry format: `id` (snake_case string), `tags` (list of 3-5 tag strings), no `incompatible_with`. Default packs use `incompatible_with` on character_dynamics only; omit from generated packs for simplicity since `_select_from_pool()` ignores it anyway.
3. Remove `inspiration.opening_situation` from both generate_pack prompt schemas — not in Inspiration model, not rendered by seed templates, not present in any default pack scenario.yaml.
4. Add ASCII/Latin character name rules to `generate_pack_user_wb.j2` for consistency with system prompt.
5. Delete dead non-wb templates (`generate_pack_system.j2`, `generate_pack_user.j2`) — zero callers in engine code, only *_wb.j2 versions are loaded by generate_pack.py.

## Non-goals

- Do not modify `_preselect_pools()` or its hash algorithm.
- Do not add `incompatible_with` support to pool selection (it's defined on PoolEntry but never enforced).
- Do not change Inspiration model or ScenarioBrief schema — only update prompt templates and delete dead files.
- Do not touch default pack scenario.yaml files.

## Risks, Ambiguities, and Blockers

- **LLM reliability**: Asking LLMs to generate 40 structured entries (10 per pool × 4 pools) in a single JSON response is expensive and may produce low-quality or malformed entries under token limits. If the LLM consistently fails or produces garbage, we may need to split into two API calls or reduce entry counts.
- **JSON parsing**: `_find_json()` was just improved with depth-counting brace matching (commit 5f38871), but a very long JSON response from generate_pack could still hit edge cases. Monitor parse success rate after deployment.
- **YAML dump size**: Default packs' scenario.yaml files are ~180 lines each. Generated packs will be similar length — no functional issue, just larger files.

## Implementation — Phase 1: Update generate_pack_system_wb.j2 schema and guidance

### Context files to load
- `ccya/prompts/generate_pack_system_wb.j2` (current file)
- `packs/default/noir-1930s/scenario.yaml` (reference for archetype pool entry format — id, tags, incompatible_with structure)

### Detailed steps

#### Step 1.1 — Remove opening_situation from Inspiration schema block

**File:** `ccya/prompts/generate_pack_system_wb.j2`, lines 46-50

**What:** In the JSON output schema's `inspiration` section, remove `"opening_sitation": "string"`. Keep only `pc`, `npcs`, `inventory`.

Before:
```json
"inspiration": {
    "pc": "string",
    "opening_situation": "string",
    "npcs": "string",
    "inventory": "string"
}
```

After:
```json
"inspiration": {
    "pc": "string",
    "npcs": "string",
    "inventory": "string"
}
```

**Why:** `opening_sitation` is not on the Inspiration Pydantic model (pack.py:123-126), not rendered by seed generation templates, and absent from all 6 default pack scenario.yaml files. It's silently dropped by pydantic — removing it from guidance prevents wasted LLM tokens and confusion.

**Validation:** `grep -n "opening_situation" ccya/prompts/generate_pack_system_wb.j2` returns no matches.

#### Step 1.2 — Add archetype pool sections to JSON output schema and guidance

**File:** `ccya/prompts/generate_pack_system_wb.j2`, after the inspiration block (after line 50 or wherever inspiration ends)

**What:** Add four new top-level fields to the JSON output schema, each requesting ~10 entries with format `{"id": "snake_case", "tags": ["tag1", ...]}`. Omit `incompatible_with` — pydantic will silently drop it if present, and `_select_from_pool()` ignores it anyway:

```json
"situation_archetypes": [
    {"id": "snake_case", "tags": ["tag1", "tag2", "tag3"]}
],
"arc_categories": [
    {"id": "snake_case", "tags": ["tag1", "tag2", "tag3"]}
],
"character_dynamics": [
    {"id": "snake_case", "tags": ["tag1", "tag2", "tag3"]}
],
"moral_pressures": [
    {"id": "snake_case", "tags": ["tag1", "tag2", "tag3"]}
]
```

Then add a guidance block after the schema and before "Output discipline":

```
## Archetype pools (4 sections, ~10 entries each)

Generate all four archetype pools. Each entry has an `id` (snake_case identifier) and `tags` (3-5 descriptive tag strings). Keep ids short and semantic; tags should capture the essence of each entry for hash-based selection during seed generation. Omit `incompatible_with`.

### Situation archetypes (~10): Opening moment pressure types — what kind of crisis or situation opens this world's story. Tags: genre-appropriate scenario descriptors.
### Arc categories (~10): Longer-term narrative directions with escalation potential — how conflicts develop and intensify over time. Tags: thematic progression patterns, conflict evolution markers.
### Character dynamics (~10): How the PC relates to power structures and other people — their position within social hierarchies and relationships. Tags: access type, alignment, resource level.
### Moral pressures (~10): Immediate ethical tensions that create compelling choices — dilemmas where every option has real costs or consequences. Tags: value conflict pairs, stakes type.

All entries must be genre-specific to this world's concept. Do not use generic or cross-genre archetypes. Each entry should feel like it could only exist in this particular setting.
```

**Why:** These four fields are consumed by `_preselect_pools()` during seed generation. Without them, generated packs fail pool pre-selection and lose all seeded context guidance (opening pressure type, arc direction, character power structures, moral tension). Default packs have 10-12 entries per pool; ask for ~10 each to match parity.

**Validation:** File renders correctly; schema block is valid JSON; guidance section is clear prose outside code blocks; `grep -n "incompatible_with" ccya/prompts/generate_pack_system_wb.j2` returns no matches (we explicitly omit it).

### Tests to write or update
None (tests temporarily removed during refactor per AGENTS.md).

### REPOMAP updates required
- None — no docs or repomap reference these template files.

## Implementation — Phase 3: Update generate_pack_user_wb.j2

### Context files to load
- `ccya/prompts/generate_pack_user_wb.j2` (current file)

### Detailed steps

#### Step 3.1 — Add JSON output discipline guidance

**File:** `ccya/prompts/generate_pack_user_wb.j2`, in the "Output discipline" section or as a new block before it

**What:** Replace existing content from line 20 through end with:

```
## Output discipline

When emitting structured data (JSON, scope tags, any machine-readable output), omit null or empty fields entirely. Do not emit `key: null` — just leave the key out.

- Wrap your entire response in a single ```json code block. Do NOT include any thinking or explanatory text outside the code block.
- All string values must use normal spaces between words — never hyphens as word separators. DO NOT replace spaces with hyphens or insert hyphens between every word.

Emit the ScenarioBrief JSON now.
```

**Why:** Consistency across all generate templates; prevents parsing failures from thinking content or malformed strings (same guidance added to seed prompts in commit 5f38871).

### Tests to write or update
None.

## Implementation — Phase 4: Verify pool loading from generated pack scenario.yaml

### Context files to load
- Any existing or newly-generated `packs/generated/*/scenario.yaml`

### Detailed steps

#### Step 4.1 — Load a generated pack's scenario.yaml and verify all 4 pools are present

**File:** Command-line verification (no code changes)

**What:** After Phases 1-3, load a generated pack's scenario.yaml through ScenarioBrief and assert all pool fields exist:

```bash
python3 -c "
import yaml, sys
from ccya.pack import ScenarioBrief

with open('packs/generated/<any-pack-id>/scenario.yaml') as f:
    data = yaml.safe_load(f) or {}

brief = ScenarioBrief(**data)
pools = {
    'situation_archetypes': len(brief.situation_archetypes),
    'arc_categories': len(brief.arc_categories),
    'character_dynamics': len(brief.character_dynamics),
    'moral_pressures': len(brief.moral_pressures),
}

for name, count in pools.items():
    if count == 0:
        print(f'FAIL: {name} is empty', file=sys.stderr)
        sys.exit(1)
    else:
        print(f'{name}: {count}')

print('All pool fields present and non-empty')
```

**Why:** Confirms the full load path works — LLM output → YAML parse → ScenarioBrief construction → all 4 pool fields populated. Without this, we can't be sure generated packs will pass `_preselect_pools()` during seed generation.

### Tests to write or update
None (tests temporarily removed per AGENTS.md). Manual verification is sufficient for now.

## Implementation — Phase 5: Delete dead non-wb templates

### Context files to load
- Confirm zero callers of generate_pack_system.j2 or generate_pack_user.j2 in engine code

### Detailed steps

#### Step 5.1 — Delete generate_pack_system.j2

**File:** `ccya/prompts/generate_pack_system.j2`

**What:** Delete this file entirely. It is never loaded by any Python code — only *_wb.j2 versions are referenced in generate_pack.py (line 76-78 and line 80-90).

**Why:** Dead code cleanup per AGENTS.md rules ("Remove dead code immediately").

#### Step 5.2 — Delete generate_pack_user.j2

**File:** `ccya/prompts/generate_pack_user.j2`

**What:** Delete this file entirely. Same reasoning as above.

**Why:** Dead code cleanup per AGENTS.md rules.

### Tests to write or update
None.

### REPOMAP updates required
- None — no docs or repomap reference these template files.
