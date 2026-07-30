# Split NPC Add/Update and Add Disposition — Design Document

> **Status:** reviewed
> **Related tickets:**
> - [F-30: Split NPC Add/Update ops and add disposition field](../../roadmap/features/F-30-split-npc-add-update-and-add-disposition.md)

## Problem

`CompendiumNpcUpdate` carries both write-once fields (motivation, fear, leverage, tie, party) and updatable fields (bio, presence, position, departed_reason). The single model forces the engine to track which fields are write-once via implicit logic in `apply_npc_scene_management()`. This is fragile and hard to reason about — the engine must guess the caller's intent from field presence.

Additionally, the personality system (archetype-based, auto-assigned from motivation/fear) was removed in I-24 but there is value in having freeform adjectives describing an NPC's speech style and demeanor to give the narrator more texture.

## Firm Decisions

1. **Split into two models** — `CompendiumNpcAdd` (seed + first appearance) and `CompendiumNpcUpdate` (subsequent scenes). Rationale: explicit intent separation eliminates the implicit write-once tracking that currently lives in `apply_npc_scene_management()`.

2. **`bio` stays in `CompendiumNpcUpdate`** — historically bios are never actually updated, and the field can remain updatable in the Update model. No change.

3. **`disposition` is a single freeform string** — no subfields. The LLM decides format (2-3 adjectives, short phrase, whatever). Rationale: freedom over structure; the narrator benefits from flexible phrasing.

4. **`disposition` is NOT guarded by the unnamed check** — unnamed NPCs get disposition just like named NPCs. Rationale: disposition describes speech style/demeanor, which is relevant even for unnamed characters.

5. **`_is_named` is already consolidated** — `npc_roster.py` imports `is_named` from `engine/utils.py` (line 9). No duplication exists. ~~Remove this decision.~~

6. **`party` is NOT currently on `CompendiumNpcUpdate`** — it exists only on `NPCEntry` in state. The design adds `party` to `CompendiumNpcAdd` as a **new capability** allowing the LLM to set party membership at NPC creation. Party remains auto-cleared on departed (engine logic) and player-managed via `POST /api/npc/{id}/toggle-party`.

## Design Principles

- **Explicit over implicit:** Each model carries only the fields it is allowed to write. No model-wide "which fields are write-once" tracking.
- **Minimal state model changes:** Add `disposition` to `NPCEntry`. Split one extraction model into two. Everything else is routing.
- **Backward compatibility not required:** This is a breaking change to extraction schemas. No migration path needed.

## Target State

### Model Changes

#### `ccya/models/extraction.py`

**Remove:** `CompendiumNpcUpdate`

**Add:** `CompendiumNpcAdd` (write-once fields):

```python
class CompendiumNpcAdd(BaseModel):
    id: str
    name: str | None = None
    title: str | None = None
    bio: str | None = None
    disposition: str | None = None
    motivation: str | None = None
    fear: str | None = None
    leverage: str | None = None
    tie: str | None = None
    party: bool = False
    first_seen_turn: int | None = None  # set by engine on initial entry creation
```

**Add:** `CompendiumNpcUpdate` (updatable fields only):

```python
class CompendiumNpcUpdate(BaseModel):
    id: str
    bio: str | None = None
    disposition: str | None = None  # updatable — LLM refines understanding
    presence: str | None = None
    position: str | None = None
    departed_reason: str | None = None
    departed_turn: int | None = None  # set by engine on first presence:"departed"
    last_seen_location: str | None = None
```

Note: `disposition` appears on **both** models. The Add model sets it at creation. The Update model allows the LLM to refine it as they learn more about the NPC.

#### `ccya/models/state.py`

**Add to `NPCEntry`:**

```python
disposition: str | None = None
```

Position: after `bio`, before `motivation`.

### Prompt Changes

#### `ccya/prompts/extract_scene_system.j2`

**Output schema (line 29-33):** Replace the single `compendium_npc_update` array with two arrays:

```json
{
  "compendium_npc_add": [
    {"id": "...", "name": "...", "title": "...", "bio": "...", "disposition": "...", "motivation": "...", "fear": "...", "leverage": "...", "tie": "..."}
  ],
  "compendium_npc_update": [
    {"id": "...", "presence": "present|nearby|known|departed", "position": "...", "bio": "...", "disposition": "...", "departed_reason": "..."}
  ]
}
```

**Field rules section (new section after line 50, before "How to use compendium_npc_update"):**

```
## Two-channel NPC extraction

Use TWO separate arrays:
- `compendium_npc_add`: NEW NPCs (first appearance only). Include `id`, `name`, `bio`, `disposition`, and psychological fields.
- `compendium_npc_update`: EXISTING NPCs (subsequent scenes). Include only fields that changed.

**Rule:** If the NPC is not in `known_characters`, put them in `compendium_npc_add`. If they exist in the compendium, put them in `compendium_npc_update`. Never put the same NPC in both arrays.

### Field definitions

- `id`: snake_case_id
- `name`: Display Name (omit if unchanged). Must be first name + surname (at least two words, no titles/prefixes).
- `title`: Optional title (omit if unchanged).
- `bio`: TWO SENTENCES: (1) appearance and demeanor — how they are physically presented, bearing/posture/expression. (2) tangible facts about who they are as a person — background details, habits, reputation. Must be relevant to the story, not generic filler like "is a merchant". Omit if unchanged.
- `disposition`: 2-3 words or short phrase describing speech style and demeanor (e.g., "Elderly, gravelly voice, hunches forward"). For new NPCs, assign alongside bio. For existing NPCs, update when narration reveals new info about how they speak or carry themselves. Omit if unchanged.
- `motivation`: what this NPC fundamentally wants. Mandatory for every character.
- `fear`: what this NPC is most afraid of.
- `leverage`: what this NPC can offer, threaten, or withhold.
- `tie`: durable personal history — to the PC, or between two NPCs (name both parties).
- `presence`: present|nearby|known|departed. REQUIRED for every NPC update — never omit it.
- `position`: Where the NPC is spatially in the scene. 5-7 words max. Only spatial location — not what they're doing. Include spatial barriers and visibility constraints. Update when narration changes the NPC's spatial location.
- `last_seen_location`: Only set when the narration explicitly places the NPC in a location different from their last. Omit if the NPC is at their last known location.
- `departed_reason`: Required when `presence` is `"departed"`. Short label followed by 1-2 sentence prose describing what happened.
```

**"How to use" section (rewrite lines 52-58):**

```
### How to use the two channels

- **New NPC enters scene:** Add to `compendium_npc_add` with `id`, `name`, `bio` (mandatory), `disposition`, and psychological fields (`motivation`, `fear`, `leverage`, `tie`). Set `presence: "present"` (in scene) or `presence: "nearby"` (same location, not interacting).
- **Existing NPC behavior changes:** Add to `compendium_npc_update` with only the changed fields (`presence`, `position`, `bio`, `disposition`).
- **Durable identity updates:** Update `bio` or `disposition` in `compendium_npc_update` when narration reveals new facts about an existing NPC. Name, title, and psychological fields (motivation, fear, leverage, tie) are write-once — set at creation via `compendium_npc_add` and not updatable after.
- **NPC unchanged:** Omit from both arrays — do not emit an update for NPCs that have no changes. **EXCEPTION:** If an NPC was previously absent or known and the narration now places them in the scene or nearby, you MUST emit an update in `compendium_npc_update` even if their other fields haven't changed.
- **Re-promotion:** If narration places an NPC in the scene, set `presence: "present"` in `compendium_npc_update`. Do NOT create a new entry — update the existing one.
```

**NPC field requirements (lines 72-75, update to include disposition):**

```
- **Named NPCs (proper name: at least two words with first and last capitalized):** Must have `bio` + `disposition` + `motivation` + 2 of {fear, leverage, tie} = 5 fields minimum. On first entry (compendium_npc_add), aim for all 5 fields. Motivation is mandatory for every character.
- **Unnamed NPCs (name does not look like a proper name — fewer than 2 words, or first/last not both capitalized):** `bio` + `disposition` + `motivation`. Do NOT add fear, leverage, or tie. Motivation is required — give them something specific and interesting, not generic filler like "maintain the peace."
```

**Dedup rule (line 68, add disposition mention):**

```
- **SAME ENTITY, DIFFERENT NAMES:** When narration mentions multiple names/titles that refer to the same entity, create ONE compendium entry with the most specific identifier. Do NOT create separate entries for what is clearly the same person.
```

#### `ccya/prompts/prepare_seed_system.j2`

**NPC schema example (line 39, add disposition):**

```json
"compendium": {"npcs": {"npc_snake_case_id": {"name": "Full display name.", "title": "Role or title.", "bio": "Biographical sketch.", "disposition": "Speech style and demeanor (e.g., 'Elderly, gravelly voice').", "presence": "present|nearby|known", "tie": "How they connect to the PC.", "motivation": "What they fundamentally want.", "fear": "What they dread.", "leverage": "What leverage they hold."}}}
```

**NPC field requirements (lines 83-98, add disposition to all categories):**

```
## NPC field requirements

- **At least 1 NPC must have `"presence": "present"`.** This is mandatory — the opening scene must include at least one NPC that is physically present.
- `presence` is required for all NPCs.
- NPCs have 5 behavioral fields (`bio`, `disposition`, `motivation`, `fear`, `leverage`) and 1 relationship field (`tie`).
  How many depends on the NPC's role:
  - **Unnamed NPCs (name does not look like a proper name):** `bio` + `disposition` + `motivation`. Do NOT add fear, leverage, or tie. Motivation is required.
  - **Named NPCs (proper name: at least two words with first and last capitalized):** Must have `bio`, `disposition`, `motivation`, and 2 of {fear, leverage, tie} — 5 fields minimum. Motivation is mandatory for every character.
  - **Important NPCs (seed characters, arc goal characters, faction leaders):** All 6 fields. These are the characters the story revolves around — give them depth.
```

### Engine Changes

#### `ccya/state/npcs.py`

**Rewrite `apply_npc_scene_management()`** to accept both `CompendiumNpcAdd` and `CompendiumNpcUpdate` lists from the extraction result.

- If an entry appears in `compendium_npc_add` (new list): create a fresh `NPCEntry` with all fields from the Add model. First-seen turn, position, color, and last_seen_location are set by the engine.
  - **Guard:** If the NPC ID already exists in the compendium, treat the Add as an **error** — log a warning and skip. Add entries must never overwrite existing NPCs. The engine should not silently wipe data.
- If an entry appears in `compendium_npc_update` (existing list): merge only the updatable fields into the existing `NPCEntry`. If the NPC does not exist, create a minimal entry (name derived from ID, presence=nearby) — this is the existing fallback behavior in `turn_state.py` line 528-543.
- If an NPC ID appears in both lists: Add wins for new NPCs. If the NPC already exists, Add is rejected (see guard above) and Update applies normally.
- Departed logic (party reset, departed_turn) applies to both paths when `presence == "departed"`.

**Move `_is_named` consolidation:** Already done — `npc_roster.py` imports from `ccya.engine.utils`.

#### `ccya/state/delta_builder.py`

- `apply_delta()` currently wraps `delta.compendium_npc_update` in a `SceneExtractResult` and passes it to `apply_npc_scene_management()`. Update to also pass `delta.compendium_npc_add` if that field is added to `StateMerge`.

#### `ccya/models/extraction.py` — `StateMerge`

**Add:** `compendium_npc_add: list[CompendiumNpcAdd] = Field(default_factory=list, max_length=6)`

#### `ccya/models/extraction.py` — `SceneExtractResult`

**Add:** `compendium_npc_add: list[CompendiumNpcAdd] = Field(default_factory=list, max_length=6)`

#### `ccya/engine/npc_roster.py`

**`build_npc_roster()`:** Include `disposition` in the output dict (line 140-155), after `bio`, before `motivation`.

**`_compute_npc_score()`:** Add `disposition` to the richness check (line 94-98) — count it as a richness field alongside motivation, fear, leverage, tie.

**Remove `_is_named` copy:** Not needed — `npc_roster.py` already imports from `ccya.engine.utils` (line 9). No action required.

#### `ccya/engine/extraction/pipeline.py`

**Dedup pass (lines 200-231):** Currently runs `_dedup_compendium_update()` on `scene_result.compendium_npc_update`. With the split, dedup must also run on `compendium_npc_add` entries — a new NPC could have a name that matches an existing compendium entry. Update the dedup loop to process both arrays. The `_dedup_compendium_update()` function signature takes `CompendiumNpcUpdate`; it needs to accept either model (or be generalized).

**Merge into StateMerge (line 241-254):** Add `compendium_npc_add=scene_result.compendium_npc_add` to the `StateMerge` constructor.

**Preview builder (line 279):** The `_apply_delta_lazy` preview uses `StateMerge(compendium_npc_update=r.compendium_npc_update or [])`. Add `compendium_npc_add=r.compendium_npc_add or []` to this preview `StateMerge` so the turn reviewer shows Add entries correctly.

#### `ccya/engine/extraction/context.py`

**`_build_post_delta_context()` (line 46-54):** The `StateMerge` constructor needs `compendium_npc_add` added so the record stream's post-delta context includes Add entries.

#### `ccya/engine/turn_state.py`

**Fallback NPC creation (lines 526-543):** This path creates a minimal `NPCEntry` when an NPC appears in `compendium_npc_update` but doesn't exist yet. With the split, `compendium_npc_add` entries should NOT hit this fallback — they go through `apply_npc_scene_management()` which handles creation properly. However, Update entries for non-existent NPCs still need this fallback. No change needed unless the fallback should also stamp `disposition`.

### I/O Changes

#### `ccya/engine/extraction/utils.py`

**`_coerce_scene_json()` (line 119-136):** Currently coerces `compendium_npc_update` entries that are strings to dicts. Add the same coercion for `compendium_npc_add` — the LLM may return string entries in the Add array too.

#### `ccya/ev/checkers/compendium_lifecycle.py`

Currently checks `applied.compendium_npc_update` to verify NPCs appear in state. With the split, this checker must also check `applied.compendium_npc_add` — new NPCs created via Add must appear in the compendium. Update `requires_fields` and the checking logic.

#### `ccya/ev/checkers/npc_presence.py`

Currently reads from `applied.compendium_npc_update`. With the split, presence changes can come from either Add (initial presence) or Update (subsequent presence changes). No change needed — this checker reads from `last_turn_state`, not the applied delta.

#### `ccya/ev/checkers/state_lifecycle.py`

Currently references `applied.compendium_npc_update` (line 133). Check if this needs updating to also reference `compendium_npc_add`.

#### `ccya/ev/prompt_context.py`

**`_build_npc_roster()`:** Include `disposition` in the output dict (line 41-55), after `bio`, before `motivation`.

#### `ccya/prompts/sections/_npc_roster.j2`

- Render `disposition` in the NPC roster line (after bio, before motivation/fear/leverage).
- Format: `— {{ n.disposition }}` when present.

## Collision / Interaction Analysis

| System | Collision | Mitigation |
|--------|-----------|------------|
| **Extraction prompt** | LLM may forget to emit `disposition` for new NPCs or confuse the two-channel split | Two-channel rule is explicit in prompt ("not in known_characters → add, exists → update"). Disposition is listed alongside bio as mandatory for new NPCs. Field count rules for named/unnamed NPCs include disposition. |
| **Seed generation** | Seed LLM may not know what `disposition` means | Schema example in `prepare_seed_system.j2` includes it; field requirements section lists it alongside motivation/fear/leverage. |
| **Delta builder** | `StateMerge` currently only carries `compendium_npc_update` | Add `compendium_npc_add` field to `StateMerge`. Update `apply_delta()` to pass both lists. |
| **Dedup pipeline** | `_dedup_compendium_update()` only processes `compendium_npc_update` | Extend dedup to also process `compendium_npc_add` entries. A new NPC could have a name matching an existing compendium entry. |
| **Extraction utils** | `_coerce_scene_json()` only coerces `compendium_npc_update` string entries | Add coercion for `compendium_npc_add` string entries too. |
| **Turn-state fallback** | `turn_state.py` creates minimal entries for Update-only NPCs | No change needed — Add entries go through `apply_npc_scene_management()` which handles creation properly. |
| **Ev checkers** | `compendium_lifecycle` only checks `applied.compendium_npc_update` | Update to also check `applied.compendium_npc_add`. |
| **Unnamed NPCs** | Previously unnamed NPCs had psychological fields stripped | Unnamed guard stays for motivation/fear/leverage/tie only. Disposition is unguarded on both Add and Update. |
| **Add-for-existing-NPC** | LLM sends Add for an NPC that already exists | Engine guard: log warning, skip. Never overwrite existing NPC data from an Add entry. |

## Risks

1. **Risk: LLM confusion from two models.** Splitting into two arrays adds prompt complexity. **Mitigation:** The prompt uses a clear two-channel rule: "If the NPC is not in `known_characters`, put them in `compendium_npc_add`. If they exist in the compendium, put them in `compendium_npc_update`." The JSON schema example reinforces the distinction. The "How to use the two channels" section gives concrete examples for each case.

2. **Risk: `disposition` on Update model creates ambiguity.** If the LLM sends `disposition` in an Update entry for an existing NPC, does it mean "refine" or "no change"? **Mitigation:** Omitting `disposition` means no change (standard extraction discipline). Including it means update. This matches the existing pattern for `bio`.

3. **Risk: Unnamed guard inconsistency.** Disposition is unguarded for unnamed NPCs while motivation/fear/leverage/tie are guarded. **Mitigation:** This is intentional. Disposition describes surface-level demeanor which is observable even without knowing a name.

3. **Risk: Unnamed guard inconsistency.** Disposition is unguarded for unnamed NPCs while motivation/fear/leverage/tie are guarded. **Mitigation:** This is intentional per user decision. Disposition describes surface-level demeanor which is observable even without knowing a name.

## Rejected Alternatives

1. **Single model with `write_once` flag per field** — Rejected: adds metadata complexity to the Pydantic model. Two models is cleaner and more explicit.

2. **Structured disposition (speech_style + demeanor + physical_tells)** — Rejected: adds rigidity. The narrator benefits from freeform phrasing. Three separate subfields would be harder for the LLM to fill consistently and harder to render in prompts.

3. **Deprecate `bio` entirely, fold into `disposition`** — Rejected: bio carries appearance + background facts; disposition carries speech style + demeanor. They serve different purposes. Bio is already established; disposition is new texture.

## Deferred Items

- **`party` field migration** — Party is currently a boolean on `CompendiumNpcUpdate`. It is auto-cleared on departed (engine logic) and managed via API. No change in this ticket. Party stays on the Add model as write-once.
- **Dispositions for departed NPCs** — No special handling for departed NPCs' dispositions. They persist in the compendium but are not rendered in the roster (departed NPCs use `departed_reason` instead of bio).
- **CompendiumNpcRemove** — No removal model. NPCs are archived via presence="archived" + departed_reason. Removing NPCs entirely is deferred.

## What an Implementer Needs to Read

1. `ccya/models/extraction.py` — current `CompendiumNpcUpdate` and `SceneExtractResult`
2. `ccya/models/state.py` — `NPCEntry` model
3. `ccya/state/npcs.py` — `apply_npc_scene_management()` (lines 26-114)
4. `ccya/state/delta_builder.py` — `apply_delta()` NPC routing (lines 267-271)
5. `ccya/engine/npc_roster.py` — `build_npc_roster()` and `is_named` copy
6. `ccya/engine/utils.py` — `is_named()` source of truth
7. `ccya/prompts/extract_scene_system.j2` — scene extraction prompt
8. `ccya/prompts/prepare_seed_system.j2` — seed prompt NPC section
9. `ccya/prompts/sections/_npc_roster.j2` — NPC roster rendering
10. `ccya/ev/prompt_context.py` — `_build_npc_roster()` for eval tooling
11. `docs/architecture/state-models.md` — state model documentation
12. `docs/repomap.md` — extraction routing section

## Dependencies on Other Designs

- None. This is a self-contained change to NPC extraction and state model.
