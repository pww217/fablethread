# NPC/Compendium Consolidation — compendium.npcs only

## Status
`completed`

## Phases

5 phases: eliminate `scene.present_npcs`, consolidate all NPC state into `compendium.npcs` with a `presence` field, remove parallel data paths, converge all prompts on a single KV lookup pattern.

Phase architecture: additive-first, cutover-last. Phase 01 adds new fields without removing old ones. Phase 02 dual-writes (maintains backward compat). Phase 03 cuts over — removes old fields from models, updates all callers and the LLM output schema prompt atomically. Phases 04-05 clean up prompts and dead references.

## Issue

The NPC system has two parallel data stores: `scene.present_npcs` (scene-specific sublist of NPC fields) and `compendium.npcs` (full permanent record). Presence is tracked implicitly by membership in `present_npcs` rather than as a field. This causes:

- **Data duplication**: name/title/bio exist in both places, enriched at some call sites but not others, creating stale or missing fields in prompts.
- **Three roster-building code paths**: `build_npc_roster()` (narrate/storytell), `_scene_npc_roster()` (extract), `_known_characters_for_extract()` with `compact=True/False` — each with different field sets.
- **Inconsistent prompt templates**: `extract_scene_user.j2` accesses `n.last_seen.location_name` while `_npc_roster.j2` accesses `n.last_seen` as plain value (renders Python repr of a dict — a bug).
- **ID leak in UI**: `{{ n.name or n.id }}` falls back to showing internal snake_case ID in ruling and extract prompts.
- **66 Python references** to `present_npcs` scattered across 15+ files, making the system fragile.

## Solution

Remove `scene.present_npcs` from state entirely. Add `presence` (PRESENT/NEARBY/KNOWN) and `notes` (scene-attitude, cleared on departure) as fields directly on each `compendium.npcs` entry. The scene extractor manages NPC state via `compendium_npc_update {presence, notes, ...}` — no separate add/remove/update channel. All prompts derive their NPC view from a single roster-building function that filters `compendium.npcs` by presence field. Name display rule: name > first alias > log error + omit. Never show `id`.

## Firm decisions

1. `scene.present_npcs` is deleted from state shape. There is no parallel list.
2. `compendium.npcs` entries gain two optional fields: `presence: str` ("present"|"nearby"|"known") and `notes: str` (scene attitude, cleared when presence→known).
3. `NpcPresence` enum stays (PRESENT/NEARBY/KNOWN) — used for the field value and roster sorting.
4. `notes` is cleared on departure (presence→known). Not folded into bio.
5. Location change sets all present NPCs' presence to "known". Next turn's scene extractor re-adds NPCs that logically follow (squadmate, escort, ally) — engine is simple, LLM handles nuance.
6. Name display rule: `name` > first `alias` > nothing (log warning, omit from roster). Never render `id`.
7. LLM output schema: `SceneExtractResult` loses `npc_add`, `npc_remove`, `npc_update`. `CompendiumNpcUpdate` gains `presence` and `notes`. The scene extractor manages all NPC state changes through this single channel.
8. NPCs with `name` missing at add time get a warning and the first alias promoted to name as fallback — never a bare `id` in prompts.
9. Last seen stamping by engine (turn.py:1254-1270) continues unchanged — it writes `last_seen` dict on touched compendium entries.
10. Phase ordering is additive-first: Phase 01 adds new fields and schema, Phase 02 dual-writes (old + new), Phase 03 cuts over (removes old fields + updates all callers + changes LLM output schema prompt atomically).

## Non-goals

- No change to the `NpcPresence` enum itself (PRESENT/NEARBY/KNOWN values remain).
- No change to `last_seen` stamping logic.
- No change to the storytell/progress step's NPC-related output schemas.
- No change to the compactor's `npc_merge` logic (still operates on compendium entries by ID).
- No new config keys.
- No change to the alias map system (`build_npc_alias_map`).
- No test creation or update (tests are temporarily removed per AGENTS.md).
- Field ownership debate (scene vs storytell) deferred — scene extractor manages all fields; storytell can update story fields (motivation/fear/leverage) when appropriate in a future change.

## Risks, Ambiguities, and Blockers

- **Migration**: Existing saves have `scene.present_npcs` data that must populate `presence`, `notes`, and `first_seen_turn` fields on compendium entries. Schema version bump v1→v2. `first_seen_turn` is set from old present_npcs[].turn_entered values during migration — this preserves the "seen since" computation for compact prompts.
- **Compactor `present_from_turn`**: Replaced by reading `first_seen_turn` directly from compendium entries (set during v1→v2 migration or on NPC creation). No separate present_npcs iteration needed.
- **Seed envelope backward compat**: Existing static packs with `SeedScene.present_npcs` will fail validation after Phase 03 removes the field from pack.py model. Since tests are temporarily removed and no one loads old-format static seeds during normal operation, this is acceptable breakage. The prompt change in Step 4.9 ensures new dynamic seeds only produce compendium.npcs entries.
- **Eval `check_npc_scene_cap`**: Must switch from `scene.present_npcs` to counting presence=present in compendium.
- **Pre/post delta state for storytell**: `_storytell_messages` needs post-delta compendium data after removal of `_ExtractionContext.present_npcs_this_turn`. Phase 03 handles this by storing a post-delta compendium reference (`comp_this_turn`).
- **Phase coordination**: Phase 03 must update models, all engine callers, and `extract_scene_system.j2` prompt atomically — one commit. Steps within Phase 03 are ordered so that caller updates (turn.py, extraction.py) happen before signature changes (narrate.py ruling.py), but since it's one atomic commit the build only breaks between phases.
- **Build must stay green between phases**: Phase 01 is additive (doesn't remove old fields). Phase 02 dual-writes (doesn't break callers). Phase 03 cuts over atomically — all changes in one commit so make check passes after completion of ALL steps in the phase.

## Implementation — Phase 01: Schema + models (additive only)

### Context files to load
- `ccya/state/io.py` (default state, migration)
- `ccya/models.py` (CompendiumNpcUpdate, NpcPresence, RosterEntry, NpcRef, SceneExtractResult, StateDelta)
- `ccya/pack.py` (CompendiumEntry, SeedCompendium, SeedScene, SeedState, SeedEnvelope)

### Detailed steps

#### Step 1.1 — Add `presence` and `notes` to CompendiumNpcUpdate

**File:** `ccya/models.py` line 223

**What:**
```python
presence: str | None = None   # "present" | "nearby" | "known" — scene extractor sets this
notes: str | None = None      # scene-specific attitude, cleared on departure
```

**Why:** CompendiumNpcUpdate becomes the universal channel for ALL NPC changes. No functional change yet — Phase 03 removes the old separate channels.

**Validation:** `make check` passes.

#### Step 1.2 — Add `first_seen_turn` to CompendiumNpcUpdate

**File:** `ccya/models.py` line 223

**What:**
```python
first_seen_turn: int | None = None  # set by engine on initial entry creation
```

**Why:** Replaces `present_from_turn` computed from `present_npcs[].turn_entered` in the compactor.

**Validation:** `make check` passes.

#### Step 1.3 — Remove `RosterEntry` dataclass

**File:** `ccya/models.py` lines 28-39

**What:** Delete the `RosterEntry` dataclass. Never imported or used.

**Why:** Dead code.

**Validation:** `grep -rn "RosterEntry" ccya/` (excluding this plan file) returns no hits. `make check` passes.

#### Step 1.4 — Schema migration v1→v2 and state default updates

**File:** `ccya/state/io.py`

**What:**
- Bump `CURRENT_SCHEMA_VERSION = 2` (line 16)
- Add `_migrate_v1_to_v2`: iterate `state["scene"]["present_npcs"]`, for each NPC, create or update `state["compendium"]["npcs"][npc["id"]]` setting:
  - `presence = "present"`
  - `notes = npc.get("notes", "")` (from present_npcs entry)
  - `first_seen_turn = npc.get("turn_entered")` — set from the turn_entered embedded in old present_npcs entries. If missing, use state.meta.turn as fallback.
- For NPCs already in compendium but not in present_npcs: if they have no presence field set, add `presence = "known"` (they existed before this save was loaded).
- If an NPC has no last_seen after migration, stamp `last_seen = {turn: state.meta.turn, location_id: state.location.id or "", location_name: state.location.name or ""}` (best-effort — handle missing location gracefully).
- Keep `"present_npcs": []` in `_default_state()` — not removed until Phase 03.

**Why:** Existing saves get their present_npcs folded into compendium entries with presence/present, notes, and first_seen_turn populated from old turn_entered values. The migration is the bridge between old list-based and new field-presence models.

**Validation:** Manual test: load old save, verify compendium entries have presence field populated from old present_npcs. `make check` passes.

#### Step 1.5 — Update pack.py models

**File:** `ccya/pack.py`

**What:**
- `CompendiumEntry` (line 44): Add optional fields `presence: str | None = None` and `notes: str | None = None`
- Keep `SeedScene.present_npcs` for now — removed in Phase 03 when the seed prompt also changes.
- Update `SeedEnvelope` docstring (line 81) to note that seed compendium entries may have presence field.

**Why:** Seed model supports the new presence field. Old `present_npcs` field kept for backward compat.

**Validation:** `make check` passes.

### Tests to write or update

No tests (per AGENTS.md).

### REPOMAP updates required

- `docs/repomap.md` line 224: Update compendium.npcs schema to include `presence`, `notes`, `first_seen_turn`
- Migration section if one exists

---

## Implementation — Phase 02: Core NPC logic (dual-write)

### Context files to load
- `ccya/state/npcs.py` (entire file)
- `ccya/engine/npc_roster.py` (entire file)
- `ccya/models.py` (CompendiumNpcUpdate, NpcAdd, NpcRemove, NpcUpdate — old fields still exist)
- `ccya/state/inventory.py` (normalize_inventory_id)

### Detailed steps

#### Step 2.1 — Rewrite `apply_npc_scene_management` with dual-write

**File:** `ccya/state/npcs.py`

**What:** Rewrite the function to process ALL NPC operations through compendium entries. It still receives `SceneExtractResult` with old `npc_add/npc_remove/npc_update` fields (they're still in the model). The function:
- For `npc_add`: upsert compendium entry with `presence="present"`, name/title/bio, and `notes`. Also add to `scene.present_npcs` list for backward compat. Stamp `first_seen_turn = current_turn_no` if new entry.
- For `npc_remove`: set `presence="known"` on compendium entry, clear `notes`, remove from `present_npcs` list.
- For `npc_update`: update compendium entry fields (name/title/bio/notes), update `present_npcs` entry. If presence was "present" and notes cleared to empty, set presence="known".
- For `compendium_npc_update`: update compendium entry fields. If `presence` is set in the update: add/remove from `present_npcs` list accordingly (presence=present → add, presence=known → remove). If presence changes present→known, clear notes on compendium entry.
- If a compendium entry gets `presence="present"` but isn't in `present_npcs`, add it to the list with id/name/title/notes fields copied from compendium.
- Enforce `NPC_SCENE_CAP`: if presence=present entries (or present_npcs length) exceeds cap, evict oldest by last_seen.turn — set them to known and clear notes.

**Fallback block update:** The existing fallback at lines 205-219 builds present_npcs from compendium when no npc deltas exist AND present_npcs is empty. Update it: check presence field first — if any compendium entry has `presence="present"`, build present_npcs from those only (not all known NPCs). If none have presence set, fall back to all known NPCs as before.

**Signature unchanged:** `(state: dict[str, Any], scene_result: SceneExtractResult, current_turn_no: int | None = None) -> dict[str, Any]`

**Why:** Dual-write maintains both systems simultaneously. Old callers still read `present_npcs` from state. New presence field is populated on all compendium entries. After Phase 03 cuts over, the `present_npcs` maintenance code is removed entirely.

**Validation:** `make check` passes. System functions identically to before — all existing callers read `present_npcs` which is still maintained.

#### Step 2.2 — Add NPC cap helper

**File:** `ccya/state/npcs.py`

**What:**
```python
def _enforce_npc_present_cap(comp: dict[str, Any]) -> int:
    """If presence=present entries exceed NPC_SCENE_CAP, evict oldest (by last_seen.turn) to known. Returns count evicted."""
```
Called at end of `apply_npc_scene_management` and on location change (Phase 03).

**Validation:** Called from step 2.1.

#### Step 2.3 — Verify alias map compatibility

**File:** `ccya/state/npcs.py` line 14

**What:** No change needed. Alias map only reads `aliases` and entry keys — new fields are invisible to it.

**Validation:** `make check` passes.

#### Step 2.4 — Rewrite `build_npc_roster` with new signature

**File:** `ccya/engine/npc_roster.py`

**What:** Replace with a compendium-only function:

```python
def build_npc_roster(
    comp: dict[str, Any],
    *,
    presence_filter: str | None = None,  # None=all
    max_entries: int = 10,
    sort_by_lru: bool = False,
    lru_order: list[str] | None = None,
) -> list[dict[str, Any]]:
```

Output shape (same as current): `{id, name, title, bio, presence, motivation, fear, leverage, bond, notes, last_seen}`. Filter by `presence_filter`. Sort: PRESENT first (by name), then NEARBY, then KNOWN. Cap at `max_entries`. When `sort_by_lru`, order by `lru_order` (most recent first) instead of name.

Keep the old function signature as a wrapper for backward compat — do NOT implement it by passing lists directly to build_npc_roster. Instead:
```python
def build_npc_roster(
    present_npcs: list[dict[str, Any]],
    known_npcs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Compat wrapper — reads from compendium internally using presence_filter logic."""
    # Build a temporary presence map: present NPCs get "present", known NPCs not in present get "known"
    present_ids = {n.get("id") for n in present_npcs if isinstance(n, dict)}
    known_ids = {n.get("id") for n in known_npcs if isinstance(n, dict)} - present_ids
    
    # Read from compendium and set presence based on which list the NPC appears in
    comp: dict[str, Any] = state["compendium"]["npcs"]  # access via closure or pass as arg
    result = build_npc_roster(
        comp, presence_filter=None, max_entries=20, sort_by_lru=False
    )
    return [r for r in result if r.get("id") in present_ids | known_ids]

```
Add `# TODO: remove compat wrapper in Phase 03`. The compat wrapper accesses the compendium from state (passed as additional arg or via closure) and filters by presence — it does NOT merge lists into a single dict. Old callers pass `(present_npcs_list, known_npcs_list)` which maps to presence values for filtering.

**Why:** New compendium-only roster builder. Compat wrapper keeps build green until Phase 03.

**Validation:** `make check` passes. Old callers still work through compat wrapper.

#### Step 2.5 — Add `get_present_npcs` convenience helper (optional, for callers that need the present list)

**File:** `ccya/state/npcs.py`

**What:**
```python
def get_present_npcs(comp: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Return (nid, entry) for all compendium entries with presence=present."""
```

**Why:** Provides a standard way for callers to get "present NPCs" without knowing about the presence field. Used by Phase 03 call sites.

**Validation:** `make check` passes.

### Tests to write or update

No tests (per AGENTS.md).

### REPOMAP updates required

- `docs/repomap.md`: Update `build_npc_roster` description (dual-signature until Phase 03)

---

## Implementation — Phase 03: Cutover (remove old system)

This is the largest phase and must be executed as one atomic change — models, engine callers, LLM output schema prompt, and `present_npcs` removal all in one commit.

### Context files to load
- `ccya/models.py` (SceneExtractResult, StateDelta, NpcAdd, NpcRemove, NpcUpdate, NpcRef)
- `ccya/state/npcs.py` (apply_npc_scene_management rewritten in Phase 02)
- `ccya/engine/npc_roster.py` (rewritten in Phase 02)
- `ccya/engine/extraction.py` (StateDelta construction, dedup, enrichment, roster building)
- `ccya/state/delta_builder.py` (location change, NPC delegation)
- `ccya/engine/turn.py` (NPC compilation, logging)
- `ccya/engine/narrate.py` (_narrate_messages, _known_characters_for_extract)
- `ccya/engine/ruling.py` (_ruling_messages present_npcs param)
- `ccya/engine/compactor.py` (present_from_map, present_npcs filtering)
- `ccya/engine/seed.py` (_sanitize_envelope)
- `ccya/prompts/extract_scene_system.j2` (LLM output schema — MUST change with models)
- `ccya/prompts/context.py` (boundary models — SceneExtractBoundary, RulingBoundary)
- `ccya/eval/universal_asserts.py` (check_npc_scene_cap, NPC name extraction)
- `ccya/state/io.py` (remove present_npcs from defaults)

### Detailed steps

#### Step 3.1 — Remove old NPC models and fields

**File:** `ccya/models.py`

**What:**
- Remove `NpcRef` (line 215), `NpcAdd` (line 235), `NpcRemove` (line 244), `NpcUpdate` (line 254) model classes.
- Remove `npc_add`, `npc_remove`, `npc_update` fields from `SceneExtractResult` (lines 320-322).
- Remove `npc_add`, `npc_remove`, `npc_update` fields from `StateDelta` (lines 295-297).
- Remove `NpcAdd`, `NpcRemove`, `NpcUpdate` from imports in both models.

**Why:** Only `compendium_npc_update` survives.

**Validation:** `make check` will FAIL at this point because callers reference removed fields. That's expected — the remaining steps in this phase update them all.

#### Step 3.2 — Remove `present_npcs` from state defaults; update migration

**File:** `ccya/state/io.py`

**What:**
- Remove `"present_npcs": []` from `_default_state()` (line 89).
- The v1→v2 migration already folds present_npcs→compendium (added in Phase 01). No change needed to migration logic.
- For NEW default state (v2+), there's no `present_npcs` key in scene.

**Validation:** New game creates state with no `scene.present_npcs`.

#### Step 3.3 — Update `apply_npc_scene_management` to compendium-only (remove dual-write)

**File:** `ccya/state/npcs.py`

**What:** Simplify `apply_npc_scene_management`:
- Remove all code paths that reference `npc_add`, `npc_remove`, `npc_update` from `SceneExtractResult`.
- Remove all code paths that read or write `state["scene"]["present_npcs"]`.
- Only process `scene_result.compendium_npc_update`: upsert compendium entries, set presence/notes/first_seen_turn, enforce cap.
- Remove the "fallback" block (lines 205-219) that builds present_npcs from compendium when present is empty — no present_npcs to maintain.

**Validation:** `make check` passes.

#### Step 3.4 — Remove `build_npc_roster` compat wrapper

**File:** `ccya/engine/npc_roster.py`

**What:** Delete the old `(present_npcs, known_npcs)` signature compat wrapper. Only the new `(comp, *, presence_filter=...)` signature remains.

**Validation:** `make check` passes.

#### Step 3.5 — Update extraction.py for compendium-only

**File:** `ccya/engine/extraction.py`

**What:**
- `_ExtractionContext` (line 40): Remove `present_npcs_this_turn`. Add `comp_this_turn: dict[str, Any] | None = None` — a read-only reference to the post-delta compendium NPC dict (`state_copy["compendium"]["npcs"]`). Do NOT mutate this dict; it is only used for reading in storytell.
- `_build_extraction_context()` (line 62): Stop extracting `present_npcs_this_turn`. Instead, store `comp_this_turn=post_state.get("compendium", {}).get("npcs", {})`. This gives storytell access to the post-delta compendium. Remove npc_add/npc_remove/npc_update from StateDelta construction (lines 76-80) — only pass `compendium_npc_update` and other non-NPC fields.
- `_dedup_compendium_add()` (line 148): Rename to `_dedup_compendium_update()`. The function's logic is identical — it checks existing NPCs by name/aliases and redirects duplicate IDs. Only difference: callers now pass `scene_result.compendium_npc_update` entries instead of `npc_add` entries. Update call site at line 715.
- **Dedup note:** There are two separate dedup paths in the current code — `_dedup_compendium_add` handles compendium_npc_update entries (line 714), while inline logic at lines 723-754 handles npc_add against compendium. After Phase 03, only the first path survives since npc_add no longer exists. The second block is removed entirely in this step.
- `_scene_npc_roster()` (line 170): Remove function entirely. It adds a `tags=["compendium"]` field to each row which NO template actually renders — it's dead data. Replace its single call site at line 231 with: `npc_roster = build_npc_roster(comp, presence_filter=None, max_entries=20)`. The output shape from build_npc_roster (id/name/title/bio/presence/motivation/fear/leverage/bond/notes/last_seen) covers everything extract_scene_user.j2 renders.
- `_extract_scene_messages()` (line 218):
  - Remove `_raw_present_npcs` and enrichment loop (lines 232-247). The old code enriched present_npcs entries with compendium name/title/bio — no longer needed since build_npc_roster reads directly from compendium. **Important:** Before removing the enrichment loop, verify that all NPCs in `scene.present_npcs` have their `name`, `title`, and `bio` fields populated in `compendium.npcs`. The apply_npc_scene_management function (Phase 02) upserts these into compendium for every npc_add/npc_update — confirm this is happening for all paths. If any present_npcs entries can exist without corresponding compendium name/title/bio, add a fallback check: `entry.get("name") or ""` in build_npc_roster (already handled by current implementation).
  - Build single NPC list: `npc_roster = build_npc_roster(comp, presence_filter=None, max_entries=20)`. This replaces BOTH the old `_scene_npc_roster` call (known_characters compact=False with full fields) AND the enrichment loop — both are now handled by one function reading from compendium.
  - Pass only `npc_roster` to template (not separate `present_npcs`). The extract_scene_user.j2 template has two NPC sections: present_npcs (line 5-8, renders id/name/title/bond/notes/last_seen) and known_characters/npc_roster (line 10-14, renders id/name/title/bio/last_seen). After consolidation with single npc_roster include, both are replaced by one unified section — the template change is in Step 4.3 but callers must stop passing present_npcs here or it becomes unused context.
- `_storytell_messages()` (line 302):
  - Build roster via `build_npc_roster(extraction_ctx.comp_this_turn, presence_filter=None, max_entries=10, sort_by_lru=True, lru_order=order)`. Reads post-delta compendium from extraction context. The compact=True behavior of the old `_known_characters_for_extract` (which limited to 10 entries and included motivation/fear/leverage but not title/bio/bond) is handled by max_entries=10 — build_npc_roster includes all fields regardless, which adds ~20-30 tokens per NPC compared to compact mode. This is acceptable since storytell already has narration context for NPCs.
  - If `comp_this_turn` is None (shouldn't happen), fall back to `build_npc_roster(state["compendium"]["npcs"], ...)` from pre-delta state.
- Line 650: Replace `present_npc_names` derivation with `[n.get("name", "") for n in extraction_ctx.comp_this_turn.values() if isinstance(n, dict) and n.get("presence") == "present"]`.
- Lines 723-754 (npc_add dedup block): Remove entirely — npc_add no longer exists. The compendium_npc_update dedup at lines 699-721 remains with renamed function.
- Lines 760-763 (npc_remove logging): Remove — npc_remove no longer exists.
- Lines 765-787 (StateDelta merge block): Stop passing `npc_add`, `npc_remove`, `npc_update`. Only pass `compendium_npc_update` and non-NPC fields.
- Line 552: Update check from `not scene_result.scene_tags and not scene_result.npc_add` to `not scene_result.scene_tags and not scene_result.compendium_npc_update`.
- Remove import of `_known_characters_for_extract` (line 18).

**Why:** The biggest consumer of dual-list NPC data. Simplified to single-source compendium reads. Post-delta compendium reference ensures storytell sees this-turn changes. Two separate dedup paths collapse into one since npc_add is eliminated.

**Validation:** `make check` passes. `grep -rn "npc_add\|npc_remove\|npc_update\|present_npcs_this_turn" ccya/engine/extraction.py` returns no hits.

#### Step 3.6 — Update delta_builder.py

**File:** `ccya/state/delta_builder.py`

**What:**
- Line 245: Replace `state.setdefault("scene", {})["present_npcs"] = []` with iterating all NPCs and setting `presence = "known"` for those with `presence == "present"`. Call `_enforce_npc_present_cap()` afterwards:
  ```python
  comp = state.setdefault("compendium", {}).setdefault("npcs", {})
  for entry in comp.values():
      if isinstance(entry, dict) and entry.get("presence") == "present":
          entry["presence"] = "known"
          entry.pop("notes", None)
  from ccya.state.npcs import _enforce_npc_present_cap
  _enforce_npc_present_cap(comp)
  ```
- Lines 333-344: Update `apply_npc_scene_management` call to not pass npc_add/npc_remove/npc_update — they no longer exist on StateDelta.

**Why:** Location change transitions NPCs by field, not by list clearing.

**Validation:** `make check` passes.

#### Step 3.7 — Update turn.py

**File:** `ccya/engine/turn.py`

**What:**
- Line 102: Remove `_compendium_bios` field from TurnContext (dead after consolidation — no template uses it).
- Line 105: Rename `_known_npcs` to `_npc_roster_known` and line 106 rename `_present_npcs` to `_npc_roster_present`. These are intermediate variables used before the single roster is built.
- Lines 883-908 (Phase 4A): Replace the entire block:
  - Remove `_known_npcs = _known_characters_for_extract(state, compact=True)` — replaced by build_npc_roster below.
  - Remove `_present_npcs = list(...)` — replaced by build_npc_roster below.
  - Remove `_compendium_bios` construction — no longer used anywhere after consolidation.
  - Build single roster: `_npc_roster = build_npc_roster(_comp, presence_filter=None, max_entries=10, sort_by_lru=True, lru_order=state.get("meta", {}).get("compendium_touch_order", []))`
- Line 955: Pass `known_npcs=_npc_roster_known, present_npcs=_npc_roster_present` — these are still passed to `_narrate_messages()` which has compat params in Phase 02. After Step 3.8 removes them from the signature, this call changes too (see step 3.8).
- Line 960: Pass only `npc_roster=_npc_roster` to `_narrate_messages` — remove `known_npcs`, `present_npcs`, `compendium_bios` params. This happens in Step 3.8 which removes the parameters from _narrate_messages signature; step 3.7 updates callers first then step 3.8 removes params — both within Phase 03 so build stays green until all steps complete.
- Remove import of `_known_characters_for_extract` (line 27).
- Line 1254-1270: `last_seen` stamping — currently stamps on `delta.npc_add/delta.npc_update`. After Phase 03 these fields no longer exist. Stamp `last_seen` on all three delta types that can create/modify NPCs:

```python
# NPCAdd entries (if any slip through before full cleanup)
for na in (delta.npc_add or []):
    touched_ids.add(na.id if hasattr(na, 'id') else None)

# NpcUpdate entries  
for nu in (delta.npc_update or []):
    touched_ids.add(nu.id)

# CompendiumNpcUpdate — the sole surviving path after Phase 03
for cu in (delta.compendium_npc_update or []):
    touched_ids.add(cu.id)
```

After full cleanup, only the `compendium_npc_update` loop remains. The other two are dead code but kept until all callers stop producing them — they serve as a safety net if any npc_add/npc_update entries leak through during transition. If you prefer to be strict and remove them immediately: stamp only on `delta.compendium_npc_update`.
- Line 1519: Change from `present_npcs_this_turn` to compendium-based present count using `[n for n in extraction_ctx.comp_this_turn.values() if isinstance(n, dict) and n.get("presence") == "present"]`.

**Why:** All NPC data from compendium. No separate lists. _compendium_bios is dead — no template renders it after consolidation (it was only used as a fallback for bio enrichment in old present_npcs logic).

**Validation:** `make check` passes. `grep -rn "present_npcs" ccya/engine/turn.py` returns no hits. `grep -rn "known_npcs\|_known_characters" ccya/engine/turn.py` returns no hits.

#### Step 3.8 — Update narrate.py

**File:** `ccya/engine/narrate.py`

**What:**
- `_narrate_messages()`: Remove `known_npcs`, `present_npcs`, `compendium_bios` parameters (lines 35-38). Only keep `npc_roster: list[dict[str, Any]] | None = None` which callers now populate. NOTE: Step 3.7 updates all callers first — both steps are in Phase 03 executed as one atomic commit so build stays green until completion.
- Remove `_known_characters_for_extract()` function entirely (lines 138-188). Replaced by `build_npc_roster(comp, presence_filter=None, max_entries=10, sort_by_lru=True, lru_order=order)`.
- Update the log line (line 52-53): remove present_npcs/known_npcs count logging. Log only: `"narrate entry turn=%d npc_roster_len=%d"`.
- Update `user_ctx` dict (line 92-118): Remove `known_npcs`, `present_npcs`, `compendium_bios` keys. NOTE: Step 4.4 removes template references to these variables — both within Phase 03/04, executed sequentially so templates aren't rendered with stale context between steps.

**Why:** Single roster source. All callers updated in step 3.7; function signature and dead params removed here.

**Validation:** `make check` passes.

#### Step 3.9 — Update ruling.py

**File:** `ccya/engine/ruling.py`

**What:**
- `_ruling_messages()` line 23: Rename parameter from `present_npcs` to `npc_roster: list[dict[str, Any]] | None = None`.
- Line 39: Change `"present_npcs": present_npcs or []` to `"npc_roster": npc_roster or []`.
- Callers in turn.py (step 3.7) already pass the right data.

**Validation:** `make check` passes.

#### Step 3.10 — Update compactor.py

**File:** `ccya/engine/compactor.py`

**What:**
- Line 228: Replace `present_from_map` construction (which iterated present_npcs for turn_entered). No present_npcs to iterate after Phase 03. Read `first_seen_turn` from each compendium entry directly — it was set during migration (Phase 01) or on NPC creation by engine:
  ```python
  compendium_npcs: list[tuple[str, Any]] = []
  for npc_id, npc_data in _npcs_raw.items():
      enriched = dict(npc_data) if isinstance(npc_data, dict) else {}
      # first_seen_turn was set during v1→v2 migration from old present_npcs[].turn_entered,
      # or on NPC creation by engine. Fall back to 0 for any entries created before this change.
      enriched.setdefault("present_from_turn", enriched.get("first_seen_turn") or 0)
      compendium_npcs.append((npc_id, enriched))
  ```
- Lines 345-351: Remove the present_npcs filtering block. Merging by ID in compendium dict handles presence implicitly — NPCs not emitted in compendium_npc_update for this turn simply aren't touched (their presence stays as-is). No separate list to clean.

**Validation:** `make check` passes. Compacted prompts show "first seen: X" instead of "seen since: X".

#### Step 3.11 — Update seed.py

**File:** `ccya/engine/seed.py`

**What:**
- `_sanitize_envelope()` (line 31):
  - Remove the present_npcs sanitization loop (lines 42-51). After Phase 03, SeedScene.present_npcs is removed from pack.py model — old static packs with this field will fail validation. Since tests are temporarily removed per AGENTS.md and no one loads old-format static seeds during normal operation, this is acceptable breakage. The prompt change in Step 4.9 ensures new dynamic seeds only produce compendium.npcs entries.
  - Iterate `envelope.seed_state.compendium.npcs` for ALL NPC entries (not just "known" ones — all NPCs generated by seed go into compendium with presence field set). Apply same surname-fallback logic and ASCII stripping to each.
  - For entries with `presence == "present"`: verify they have a `notes` field; if not, set default notes based on NPC's role/title (e.g., `"A companion in the current scene"`).

**Why:** Seed generates single-block compendium output only. No separate present_npcs list. Old static pack format is abandoned — any existing packs with present_npcs must be regenerated via prompt change (Step 4.9) or manually updated.

**Validation:** `make check` passes.

#### Step 3.12 — Update `extract_scene_system.j2` (LLM output schema)

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Major rewrite:
- Remove all instructions about `npc_add`, `npc_remove`, `npc_update` output schema.
- Update output schema section: only `compendium_npc_update` (with `presence`, `notes` fields added).
- Rewrite rules section:
  - "To add an NPC to the scene, emit `compendium_npc_update` with `presence: 'present'` and set `notes` to their current attitude/situation."
  - "To remove an NPC from the scene, emit `compendium_npc_update` with `presence: 'known'` — their `notes` will be cleared."
  - "To update an NPC's bio, name, title, aliases, or story fields (allegiance, motivation, fear, leverage), emit `compendium_npc_update` with the changed fields."
  - "To introduce a new NPC never seen before, emit `compendium_npc_update` with a new `id`, their `name`, `bio`, `title`, `presence: 'present'`, and `notes`."
- Update dedup rules: "Check the character roster for existing NPCs by name or alias. If a match exists, reuse their existing ID — do not create a new one."
- Keep the NPC cap guidance (max new NPCs per turn, ambient presence rules, etc.).
- Remove the `## State-presence rule` duplicate section if one exists.

**Why:** LLM output schema changed — only `compendium_npc_update` remains. This MUST change simultaneously with the model field removal (Step 3.1) or the LLM will emit fields the engine rejects.

**Validation:** Review rendered output against new `SceneExtractResult` schema.

#### Step 3.13 — Update context.py boundary models

**File:** `ccya/prompts/context.py`

**What:**
- `RulingBoundary` (line 202): Rename `present_npcs: list[NPCRosterEntryBlock]` to `npc_roster: list[NPCRosterEntryBlock]`. The ruling_user.j2 template renders this as `{{ npc_roster }}` — matching the param rename in ruling.py step 3.9 and turn.py caller update step 3.7. Update TEMPLATE_CONTRACTS mapping if present.
- `SceneExtractBoundary` (line 243): Remove `present_npcs: list[NPCRosterEntryBlock]` field entirely. The extract_scene_user.j2 template currently renders BOTH fields — `npc_roster` as known_characters section and `present_npcs` as the present NPCs section (lines 5-8 and 10-14). After consolidation in Step 4.3, only npc_roster is rendered. Remove both from boundary model since they're replaced by single `npc_roster: NPCRosterBlock`. Update docstring comment on line 247 to reflect new source: "npc_roster comes from build_npc_roster(comp, presence_filter=None) — outputs dicts with id/name/title/bio/presence/mfl/notes/last_seen."
- `NarratorBoundary` (line 216): Update docstring comment — remove mention of dead `present_npcs`/`known_npcs` fields in the NOTE line. The template now uses only npc_roster from build_npc_roster().

**Why:** Boundary models must match single-roster template contract after consolidation. SceneExtractBoundary had two NPC data sources (both rendered) — both collapse to one.

**Validation:** `make check` passes.

#### Step 3.14 — Update eval assertions

**File:** `ccya/eval/universal_asserts.py`

**What:**
- `check_npc_scene_cap` (line 452): Switch from `len(scene.get("present_npcs"))` to counting compendium entries with `presence == "present"`.
- Lines 347-351: Change from reading `scene.get("present_npcs")` to reading `compendium.npcs` with presence=present filter.
- Line 321: Remove present_npcs reference from docstring.

**Validation:** `grep -rn "present_npcs" ccya/eval/` returns no hits.

### Tests to write or update

No tests (per AGENTS.md).

### REPOMAP updates required

- `docs/repomap.md`: State shape — remove `present_npcs` from scene, add `presence/notes/first_seen_turn` to compendium entries
- `docs/repomap.md`: Update NPC_SCENE_CAP description
- `docs/repomap.md`: Extraction pipeline — note that scene stream only emits `compendium_npc_update`
- `docs/repomap.md`: Seed pipeline — remove `present_npcs` reference

---

## Implementation — Phase 04: Prompt consolidation

### Context files to load
- `ccya/prompts/context.py` (TEMPLATE_CONTRACTS)
- `ccya/prompts/sections/_npc_roster.j2`
- `ccya/prompts/sections/_npc_roster_extract.j2`
- `ccya/prompts/extract_scene_user.j2`
- `ccya/prompts/narrate_user.j2`
- `ccya/prompts/narrate_system.j2`
- `ccya/prompts/storytell_user.j2`
- `ccya/prompts/ruling_user.j2`
- `ccya/prompts/compact_user.j2`
- `ccya/prompts/generate_seed_system.j2`
- `ccya/prompts/generate_seed_user.j2`
- `ccya/prompts/compact_system.j2`

### Detailed steps

#### Step 4.1 — Consolidate roster templates

**File:** `ccya/prompts/sections/_npc_roster.j2`

**What:** Update to be the single roster template:
- Add `id` rendering: `` `{{ n.id }}` | **{{ n.name }}** `` with Jinja guard: ``{% if n.name %}**{{ n.name }}**{% else %}[Unnamed]{% endif %}` — never render raw id as name.
- Fix `last_seen` rendering: use `n.last_seen.location_name` when dict, fall back to string value (e.g., `"unknown"` or `"?"`). Current code accesses `.location_name` on a plain string which crashes; the fix handles both types: ``{% if n.last_seen is mapping %}{{ n.last_seen.location_name }}{% else %}{{ n.last_seen | default('?') }}{% endif %}``.
- Include notes, motivation, fear, leverage, bond inline (all optional) — render only when truthy.
#### Step 4.1 — Consolidate roster templates

**File:** `ccya/prompts/sections/_npc_roster.j2`

**What:** Update to be the single roster template:
- Add `id` rendering: `` `{{ n.id }}` | **{{ n.name }}** `` with Jinja guard: ``{% if n.name %}**{{ n.name }}**{% else %}[Unnamed]{% endif %}` — never render raw id as name.
- Fix `last_seen` rendering: use `n.last_seen.location_name` when dict, fall back to string value (e.g., `"unknown"` or `"?"`). Current code accesses `.location_name` on a plain string which crashes; the fix handles both types: ``{% if n.last_seen is mapping %}{{ n.last_seen.location_name }}{% else %}{{ n.last_seen | default('?') }}{% endif %}``.
- Include notes, motivation, fear, leverage, bond inline (all optional) — render only when truthy.
- Remove narrate-specific instruction "Before introducing a new named NPC, check this list first" — belongs in system prompt.

**Why:** Single template for all prompts. Consistent field rendering. Jinja guard prevents leaking internal IDs as names. Dict-aware last_seen access prevents crashes on string values.

#### Step 4.2 — Remove `_npc_roster_extract.j2`

**File:** `ccya/prompts/sections/_npc_roster_extract.j2`

**What:** Delete the file. Replace its include in `storytell_user.j2` with the consolidated `_npc_roster.j2`.

**Token impact note:** `_npc_roster_extract.j2` rendered compact rows (id/name only, no motivation/fear/leverage/bond). The full `_npc_roster.j2` renders all fields. Expect ~15-30 extra tokens per NPC in storytell prompts — acceptable since storytell already has narration context for each NPC and the richer data improves continuity.

**Why:** Single roster template eliminates duplication. Token increase is small relative to total prompt size (~4k-6k tokens).

#### Step 4.3 — Rewrite `extract_scene_user.j2`

**What:** Remove separate `present_npcs` and `known_characters` sections (lines 5-14). Replace with a single `{% include "sections/_npc_roster.j2" %}` after the location block. The roster is built from compendium in Phase 03 (step 3.5 — callers pass only npc_roster, not separate present_npcs).

**Rendering shape change:** Old template had two sections: `present_npcs` rendered as `` `id` | **name or id** (title) [bond] — notes -- last seen in location_name`` and `known_characters/npc_roster` rendered as `` `id` | name or id (title) — bio -- last seen in: location_name``. After consolidation, single section renders: ``**name** (title) [PRESENT/NEARBY/KNOWN] — bio | notes | wants/fears/leverage/bond | last_seen: location_name``. The ID fallback (`n.name or n.id`) is eliminated per firm decision #6 — name is always present after engine enrichment in Phase 03. If a template consumer needs the raw id for reference, add `` `{{ n.id }}` `` prefix to roster template (handled in Step 4.1).

#### Step 4.4 — Update `narrate_user.j2`

**What:** Line 13: Include uses consolidated `_npc_roster.j2` (already the case). Remove any references to `known_npcs` or `present_npcs` — they're no longer in the context dict.

#### Step 4.5 — Update `narrate_system.j2`

**What:** Add name display instruction: "Always refer to NPCs by their proper name (first and last). Descriptive labels like 'scarred veteran' are aliases, not names — use the NPC's real name in narration."

#### Step 4.6 — Update `storytell_user.j2`

**What:** Line 1: Change include from `_npc_roster_extract.j2` to `sections/_npc_roster.j2`.

#### Step 4.7 — Update `ruling_user.j2`

**What:**
- Line 10: Change `present_npcs` variable reference to `npc_roster` (matching RulingBoundary rename in step 3.13 and ruling.py param rename in step 3.9).
- Line 12: Change `` {{ n.name or n.id }}`` — per firm decision #6, name is always present after engine enrichment. Use just `{{ n.name }}`. If for some reason name is missing (shouldn't happen), use Jinja guard: `{% if n.name %}{{ n.name }}{% else %}[Unnamed]{% endif %}` to avoid leaking internal snake_case IDs into prompts.

#### Step 4.8 — Update `compact_user.j2`

**What:** Line 41: Change `npc.get("present_from_turn", "?")` to `npc.get("first_seen_turn", "?")` and change display text from "seen since" to "first seen".

#### Step 4.9 — Update `generate_seed_system.j2`

**What:** Replace separate `## present_npcs` and `## compendium.npcs` sections with single `## compendium.npcs`:
- "Generate 4-5 named NPCs total: 2 with `presence='present'` and 2-3 with `presence='known'`."
- "NPCs with `presence='present'` must have `notes` describing their current attitude/situation."
- "Descriptive labels like 'scarred veteran' belong in `aliases`, not `name`. All NPC names must be a given name and a family name."

#### Step 4.10 — Update `generate_seed_user.j2`

**What:** Line 69: Change "Generate exactly that many present_npcs entries" to "Generate exactly that many NPCs with `presence='present'`."

#### Step 4.11 — Update `compact_system.j2`

**What:** Review for any references to `present_npcs` or present NPC management. Likely no changes needed — the compactor operates on compendium entries by ID.

### Tests to write or update

No tests (per AGENTS.md).

### REPOMAP updates required

- `docs/repomap.md`: Update generate_seed_system.j2 description
- `docs/repomap.md`: Update extract_scene_user.j2 description

---

## Implementation — Phase 05: Cleanup

### Context files to load
- `scripts/debug/ev.py` (present_npcs display and diff references)
- `docs/repomap.md` (full file for final update)
- `ccya/state/io.py` (verify no stale defaults)

### Detailed steps

#### Step 5.1 — Update ev.py debug script

**File:** `scripts/debug/ev.py`

**What:**
- Line 935: Replace `present_npcs = scene.get("present_npcs", [])` with reading compendium entries where `presence == "present"`.
- Line 1031: Update `present_npcs_this_turn` diff key — change to `npcs_present` or similar.
- Lines 1530, 1534, 1900, 2008: All `present_npcs_this_turn` references → compendium-based equivalent.

**Validation:** `grep -rn "present_npcs" scripts/debug/` returns no hits.

#### Step 5.2 — Remove `present_npcs` from test conftest

**File:** `tests/conftest.py`

**What:** Remove `"present_npcs": []` from test state fixtures.

#### Step 5.3 — Final `docs/repomap.md` update

**File:** `docs/repomap.md`

**What:** Ensure every module description matches the compendium-only NPC system. Remove all references to `present_npcs`, `npc_add`, `npc_remove`, `npc_update`, `NpcRef`, `RosterEntry`.

#### Step 5.4 — Verify `scene.turn_entered` is still used

**File:** `ccya/state/io.py`, `docs/repomap.md`

**What:** Confirm that `scene.turn_entered` (set in delta_builder.py:247) is still needed by turn.py for scene age computation. It IS used — **do not remove it**. Only the NPC-level `turn_entered` (embedded in old present_npcs entries, now replaced by first_seen_turn on compendium entries) is gone. The scene-level field stays unchanged.

**Note:** `scene.location_entered_turn` (set in delta_builder.py:248) is written but not read anywhere except test fixtures and eval trace artifacts. It's dead code — out of scope for this NPC consolidation change. Leave it as-is; a separate cleanup PR can remove it later.

### Tests to write or update

No tests (per AGENTS.md).

### REPOMAP updates required

- Full `docs/repomap.md` review
