# Plan: F-30 — Split NPC Add/Update ops and add disposition field

## Design Reference

- Design: `docs/design/F-30-split-npc-add-update-and-disposition.md`

## Problem Statement

`CompendiumNpcUpdate` carries both write-once fields (motivation, fear, leverage, tie, party) and updatable fields (bio, presence, position, departed_reason). The single model forces the engine to track which fields are write-once via implicit logic in `apply_npc_scene_management()`. This is fragile and hard to reason about. Additionally, there is no `disposition` field for freeform NPC personality descriptors (speech style, demeanor) that give the narrator more texture.

## Firm decisions (from design)

1. **Split into two models** — `CompendiumNpcAdd` (seed + first appearance, write-once fields) and `CompendiumNpcUpdate` (subsequent scenes, updatable fields only).
2. **`bio` stays in `CompendiumNpcUpdate`** — historically bios are never actually updated, but the field can remain updatable in the Update model.
3. **`disposition` is a single freeform string** — no subfields. The LLM decides format.
4. **`disposition` is NOT guarded by the unnamed check** — unnamed NPCs get disposition just like named NPCs.
5. **`_is_named` is already consolidated** — `npc_roster.py` imports `is_named` from `engine/utils.py`. No duplication exists.
6. **`party` is NOT on `CompendiumNpcUpdate`** — it exists only on `NPCEntry` in state. The design adds `party` to `CompendiumNpcAdd` as a new capability.
7. **Add-for-existing-NPC guard** — if an Add entry targets an existing NPC, log a warning and skip. Never overwrite existing NPC data.

## Scope

- **Phase 01:** Model changes — split `CompendiumNpcUpdate` into Add/Update, add `disposition` to `NPCEntry`, add `compendium_npc_add` to `StateMerge` and `SceneExtractResult`, update exports.
- **Phase 02:** Extraction pipeline + prompt changes — dedup pipeline handles Add array, coerce utils handles Add, merge into StateMerge includes Add, post-delta context includes Add, preview builder includes Add, scene extraction prompt updated for two-channel schema, seed prompt updated for disposition.
- **Phase 03:** Engine + state management — `apply_npc_scene_management()` handles both Add and Update lists with write-once semantics and unnamed guard, `_npc_roster.j2` renders disposition, `build_npc_roster()` includes disposition, `_compute_npc_score()` counts disposition as richness field, prompt_context includes disposition.
- **Phase 04:** Ev tooling — `compendium_lifecycle` checker handles Add entries, `state_lifecycle` checker reviewed for Add references.
- **Documentation:** `state-models.md` updated for new models and field routing, `repomap.md` updated for extraction routing changes.

## Status

`scoping`

---

## Phase 01: Model changes

### Depends on

None

### Context files to load

- `fablethread/models/extraction.py:18-32` — current `CompendiumNpcUpdate` model (to be replaced)
- `fablethread/models/extraction.py:109-112` — `SceneExtractResult` (add `compendium_npc_add`)
- `fablethread/models/extraction.py:75-94` — `StateMerge` (add `compendium_npc_add`)
- `fablethread/models/state.py:77-95` — `NPCEntry` (add `disposition`)
- `fablethread/models/__init__.py:9-12` — exports (add `CompendiumNpcAdd`)

### What changes

**Remove `CompendiumNpcUpdate`** from `fablethread/models/extraction.py` and **replace with two models**: `CompendiumNpcAdd` and `CompendiumNpcUpdate`.

**`CompendiumNpcAdd`** (write-once fields):
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
    first_seen_turn: int | None = None
```

**`CompendiumNpcUpdate`** (updatable fields only):
```python
class CompendiumNpcUpdate(BaseModel):
    id: str
    bio: str | None = None
    disposition: str | None = None
    presence: str | None = None
    position: str | None = None
    departed_reason: str | None = None
    departed_turn: int | None = None
    last_seen_location: str | None = None
```

**Add `disposition` to `NPCEntry`** in `fablethread/models/state.py`, after `bio`, before `motivation`:
```python
disposition: str | None = None
```

**Add `compendium_npc_add` to `StateMerge`** in `fablethread/models/extraction.py`:
```python
compendium_npc_add: list[CompendiumNpcAdd] = Field(default_factory=list, max_length=6)
```

**Add `compendium_npc_add` to `SceneExtractResult`** in `fablethread/models/extraction.py`:
```python
compendium_npc_add: list[CompendiumNpcAdd] = Field(default_factory=list, max_length=6)
```

**Export `CompendiumNpcAdd`** from `fablethread/models/__init__.py`.

### Why

Two models explicitly separate write-once from updatable fields. `disposition` provides freeform NPC personality texture. `compendium_npc_add` carries the new Add entries through the pipeline.

### Validation

- `make check` passes (lint + typecheck)
- `CompendiumNpcAdd` and `CompendiumNpcUpdate` importable from `fablethread.models`
- `NPCEntry` has `disposition` field with default `None`

---

## Phase 02: Extraction pipeline + prompt changes

### Depends on

Phase 01

### Context files to load

- `fablethread/engine/extraction/pipeline.py:212-231` — dedup loop (processes `compendium_npc_update`, needs Add)
- `fablethread/engine/extraction/pipeline.py:241-254` — StateMerge merge (needs Add)
- `fablethread/engine/extraction/pipeline.py:279` — preview builder (needs Add)
- `fablethread/engine/extraction/context.py:46-54` — post-delta context StateMerge (needs Add)
- `fablethread/engine/extraction/utils.py:88-116` — `_dedup_compendium_update()` (type signature, needs Add support)
- `fablethread/engine/extraction/utils.py:119-136` — `_coerce_scene_json()` (needs Add coercion)
- `fablethread/prompts/extract_scene_system.j2` — scene extraction prompt (two-channel schema)
- `fablethread/prompts/prepare_seed_system.j2` — seed prompt (disposition in schema + field requirements)

### What changes

**Dedup pipeline** (`pipeline.py:212-231`):
- Extend the dedup loop to process `compendium_npc_add` entries in addition to `compendium_npc_update`.
- A new NPC could have a name that matches an existing compendium entry.
- The `_dedup_compendium_update()` function in `utils.py` takes `CompendiumNpcUpdate` — generalize its type hint to accept `CompendiumNpcAdd | CompendiumNpcUpdate`.
- Create a dedup pass for Add entries with its own redirect tracking.

**Coerce utils** (`utils.py:119-136`):
- Add coercion for `compendium_npc_add` string entries in `_coerce_scene_json()`, mirroring the existing `compendium_npc_update` coercion.

**Merge into StateMerge** (`pipeline.py:241-254`):
- Add `compendium_npc_add=scene_result.compendium_npc_add` to the `StateMerge` constructor.

**Post-delta context** (`context.py:46-54`):
- Add `compendium_npc_add=list(scene_result.compendium_npc_add or [])` to the `StateMerge` constructor.

**Preview builder** (`pipeline.py:279`):
- Add `compendium_npc_add=r.compendium_npc_add or []` to the preview `StateMerge` in `_scene_stream()`.

**Scene extraction prompt** (`extract_scene_system.j2`):
- Replace single `compendium_npc_update` array in output schema with two arrays: `compendium_npc_add` and `compendium_npc_update`.
- Add "Two-channel NPC extraction" section explaining the rule: "If the NPC is not in `known_characters`, put them in `compendium_npc_add`. If they exist in the compendium, put them in `compendium_npc_update`."
- Add field definitions for both models.
- Add "How to use the two channels" section with concrete examples.
- Update NPC field requirements: named NPCs need `bio` + `disposition` + `motivation` + 2 of {fear, leverage, tie} = 5 fields minimum. Unnamed NPCs get `bio` + `disposition` + `motivation`.
- Update dedup rule to mention disposition.
- Remove "UNIVERSAL NPC CHANNEL" language — replace with two-channel language.

**Seed prompt** (`prepare_seed_system.j2`):
- Add `disposition` to the NPC schema example.
- Add `disposition` to all NPC field requirement categories (unnamed, named, important).
- Add disposition to the "NPCs have X behavioral fields" count (now includes disposition).

### Why

The pipeline must understand the two-channel split to dedup, coerce, merge, and preview correctly. The prompts must instruct the LLM on the new schema and field requirements.

### Validation

- `make check` passes
- Dedup processes both Add and Update arrays
- Coerce handles string entries in Add array
- StateMerge carries both arrays
- Post-delta context includes Add entries
- Preview builder shows Add entries
- Prompt renders correctly with two-channel schema

---

## Phase 03: Engine + state management

### Depends on

Phase 02

### Context files to load

- `fablethread/state/npcs.py:26-114` — `apply_npc_scene_management()` (rewrite for dual-write)
- `fablethread/state/delta_builder.py:267-271` — `apply_delta()` NPC routing (pass Add list)
- `fablethread/prompts/sections/_npc_roster.j2` — NPC roster rendering (add disposition)
- `fablethread/engine/npc_roster.py:75-98` — `_compute_npc_score()` (add disposition to richness)
- `fablethread/engine/npc_roster.py:139-155` — `build_npc_roster()` (add disposition to output)
- `fablethread/ev/prompt_context.py:33-58` — `_build_npc_roster()` (add disposition)

### What changes

**`apply_npc_scene_management()`** (`npcs.py:26-114`):
- Accept both `compendium_npc_add` and `compendium_npc_update` lists from the extraction result.
- **Add path:** For each entry in `compendium_npc_add`, create a fresh `NPCEntry` with all fields from the Add model. Stamp `first_seen_turn`, `last_presence_turn`, `last_seen_location`, `color` by the engine.
  - **Guard:** If the NPC ID already exists in the compendium, log a warning and skip. Never overwrite existing NPC data from an Add entry.
- **Update path:** For each entry in `compendium_npc_update`, merge only the updatable fields (`bio`, `disposition`, `presence`, `position`, `departed_reason`, `departed_turn`, `last_seen_location`) into the existing `NPCEntry`. If the NPC does not exist, create a minimal entry (name derived from ID, presence=nearby) — this is the existing fallback behavior.
- **Both lists:** If an NPC ID appears in both, Add is rejected (see guard) and Update applies normally.
- **Departed logic:** Party reset, `departed_turn` stamping apply to both paths when `presence == "departed"`.
- **Unnamed guard:** Strip `motivation`, `fear`, `leverage`, `tie` if `_is_named()` returns false. **Disposition is NOT stripped** — it is unguarded per design decision.
- Function signature changes: the `scene_result` parameter is already `SceneExtractResult` which now has both lists.

**`apply_delta()`** (`delta_builder.py:267-271`):
- Pass `compendium_npc_add` to `SceneExtractResult` when calling `apply_npc_scene_management()`:
  ```python
  SceneExtractResult(
      compendium_npc_update=delta.compendium_npc_update or [],
      compendium_npc_add=delta.compendium_npc_add or [],
  )
  ```

**`_npc_roster.j2`**:
- Render `disposition` in the NPC roster line, after bio, before motivation/fear/leverage.
- Format: `— {{ n.disposition }}` when present.
- Insert after the bio rendering: `{% if n.disposition %} — {{ n.disposition }}{% endif %}`

**`build_npc_roster()`** (`npc_roster.py:139-155`):
- Add `disposition` to the output dict, after `bio`, before `motivation`.

**`_compute_npc_score()`** (`npc_roster.py:94-98`):
- Add `disposition` to the richness check — count it as a richness field alongside motivation, fear, leverage, tie.

**`_build_npc_roster()`** (`prompt_context.py:41-55`):
- Add `disposition` to the output dict, after `bio`, before `motivation`.

### Why

The engine must handle the two-channel split at the state mutation level. The roster rendering must show disposition. The richness scoring must account for disposition.

### Validation

- `make check` passes
- Add entries create new NPCs with all fields
- Add-for-existing-NPC guard prevents data overwrite
- Update entries merge only updatable fields
- Departed logic works for both paths
- Unnamed guard strips psychological fields but NOT disposition
- Roster renders disposition
- Richness scoring includes disposition

---

## Phase 04: Ev tooling

### Depends on

Phase 03

### Context files to load

- `fablethread/ev/checkers/compendium_lifecycle.py:12-16` — checker registration (requires_fields, description)
- `fablethread/ev/checkers/compendium_lifecycle.py:23-49` — checker logic (iterates `compendium_npc_update`)
- `fablethread/ev/checkers/state_lifecycle.py:131-133` — `npc_presence_decay` checker (reviews for Add references)

### What changes

**`compendium_lifecycle` checker** (`compendium_lifecycle.py`):
- Update `requires_fields` to include `"applied.compendium_npc_add"`.
- Update description to mention both Add and Update.
- Iterate over both `applied.compendium_npc_add` and `applied.compendium_npc_update` to verify NPCs appear in `state.compendium.npcs`.

**`npc_presence_decay` checker** (`state_lifecycle.py:131-133`):
- Review `requires_fields` — currently `["last_turn_state", "applied.compendium_npc_update"]`. This checker reads from `last_turn_state`, not the applied delta. The `applied.compendium_npc_update` reference is for the location_change context. No change needed if the checker only validates state, not deltas.

### Why

Ev checkers must validate the new model paths. NPCs created via Add must appear in state just like NPCs created via Update.

### Validation

- `make check` passes
- `compendium_lifecycle` checker passes on runs with Add entries
- `npc_presence_decay` checker unaffected

---

## Documentation updates

- `docs/architecture/state-models.md` — add `CompendiumNpcAdd` model, update `CompendiumNpcUpdate` model, add `disposition` to `NPCEntry` description, update `SceneExtractResult` to show both arrays, update `StateMerge` to show `compendium_npc_add`.
- `docs/repomap.md` — update extraction routing section to mention two-channel NPC extraction, update `SceneExtractResult` description, update `StateMerge` description.
- `AGENTS.md` — update extraction routing section in "Any cross-cutting tasks" to mention two-channel NPC extraction.
