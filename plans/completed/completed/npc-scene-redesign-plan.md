# NPC Scene Redesign Plan

**Design Reference:** `docs/design/npc-scene-redesign-design.md`
**Ticket:** `roadmap/features/npc-scene-redesign.md`

## Phase Summary

Eight phases ordered by dependency: models first, then engine modules (npcs → seed → extraction → roster), then prompts, then server/templates, then exports and docs. Each phase is independently executable and testable. The core changes are: remove `aliases` field entirely, drop plural/group NPC logic, replace alias-based unnamed detection with proper-name heuristic (2+ words, first and last capitalized), remove ambient NPC requirement, add scene NPC count guidance to prompts.

---

## Phase 01: Models

**File:** `ccya/models/extraction.py`

**What:** Remove `aliases: list[str] = Field(default_factory=list)` from `CompendiumNpcUpdate` (line 23).

**Why:** D1 — aliases field is removed entirely. This is the Pydantic model that the scene extractor outputs. Removing it means the LLM schema in prompts must also stop referencing it.

**Validation:** `CompendiumNpcUpdate` no longer has an `aliases` attribute. Any code referencing `comp_upd.aliases` will fail at import/runtime — catch these in subsequent phases.

---

## Phase 02: Engine — NPC Management

**File:** `ccya/state/npcs.py`

**What:**
- Remove `_STRIPPLABLE_QUANTITIES` constant (lines 17-22).
- Remove `build_npc_alias_map` function (lines 25-73).
- Remove `_resolve_group_npc_id` function (lines 76-107).
- Remove `_strip_quantity_suffix` function (lines 128-143).
- Remove `_find_npc_by_name` function (lines 146-169).
- Add `_is_named(name: str) -> bool` proper-name heuristic:
  ```python
  def _is_named(name: str) -> bool:
      if not name:
          return False
      words = name.strip().split()
      if len(words) < 2:
          return False
      return words[0] and words[0][0].isupper() and words[-1] and words[-1][0].isupper()
  ```
- In `apply_npc_scene_management`:
  - Remove `alias_map = build_npc_alias_map(comp)` call.
  - Remove `_resolve_group_npc_id` call and all name-based resolution using alias_map.
  - Remove quantity-embedded ID consolidation / merge logic (lines 205-239).
  - Remove alias merging on lines 256-261.
  - Replace unnamed guard (lines 263-276) with: `_is_unnamed = comp_upd.name and not _is_named(comp_upd.name)`.
  - Remove alias-based personality assignment logic (lines 286-303): replace quantity-stripped name matching and alias-based unnamed check with `_is_named` check.
  - Remove alias-based unnamed check in engine fallback personality assignment (lines 306-308): replace with `_is_named(entry.get("name", ""))`.
  - Remove `name_alias in alias_map` check (lines 197-199).
  - Remove `_find_npc_by_name` call (lines 201-203).

**Why:** D1 + D2 — Remove all alias map, group NPC resolution, quantity stripping. Replace unnamed detection with proper-name heuristic.

**Validation:** `apply_npc_scene_management` no longer references `build_npc_alias_map`, `_resolve_group_npc_id`, `_strip_quantity_suffix`, `_find_npc_by_name`, or `aliases`. The `_is_named` function is used for unnamed detection.

---

## Phase 03: Engine — Seed

**File:** `ccya/engine/seed.py`

**What:**
- Remove `_QUANTITY_WORDS` constant (line 307).
- Remove alias-based unnamed detection in the post-processing loop (lines 307-317):
  - Remove the quantity-stripping logic.
  - Remove the alias-matching unnamed check.
  - Keep the personality assignment logic (lines 318-337) but replace the unnamed check with `_is_named`.
- Add `_is_named` function at module level.
- In `_sanitize_envelope`: Remove the single-part name fixup logic (lines 49-53) that appends a surname hash — the seed prompt now enforces two-part names.

**Why:** D1 + D2 + D3 — Remove quantity words and alias-based unnamed detection. Replace with proper-name heuristic. Seed prompt enforces two-part names so the hash-based fixup is unnecessary.

**Validation:** Seed generation no longer references `_QUANTITY_WORDS` or alias-based unnamed detection. `_is_named` is used instead.

---

## Phase 04: Engine — Extraction

**Files:** `ccya/engine/extraction/utils.py`, `ccya/engine/extraction/context.py`, `ccya/engine/extraction/pipeline.py`

### utils.py

**What:**
- Remove `_GROUP_QUANTIFIERS` constant (lines 82-88).
- Remove `_extract_group_base_type` function (lines 91-108).
- Simplify `_dedup_compendium_update`:
  - Remove group NPC base type matching (lines 143-152).
  - Remove alias matching from `npc_names` list (line 137: remove `[a or ""... for a in (npc.get("aliases") or [])]`).
  - Add case-insensitive name matching: compare `candidate` against `npc.get("name", "").lower()` and `npc.get("id", "").lower().replace("_", " ")`.
  - Keep: exact name match check (lines 139-141).
  - Remove: group NPC base type match.

### context.py

**What:**
- In `_filter_unnamed_personality` (lines 80-106):
  - Remove alias-based unnamed detection (lines 97-98: `aliases = [...]`, `is_unnamed = name and aliases and ...`).
  - Add `_is_named` import or inline the heuristic.
  - Replace with: `is_unnamed = name and not _is_named(name)`.

### pipeline.py

**What:**
- Remove `aliases` extraction from `existing_npcs` dict (line 304: `"aliases": list(npc.get("aliases") or [])`).

**Why:** D1 + D2 — Remove group quantifiers, simplify dedup to case-insensitive name matching. Replace unnamed detection with proper-name heuristic. Remove aliases from pipeline context building.

**Validation:** `_dedup_compendium_update` no longer references `_GROUP_QUANTIFIERS`, `_extract_group_base_type`, or `aliases`. `_filter_unnamed_personality` uses `_is_named`. Pipeline no longer extracts `aliases` from existing NPCs.

---

## Phase 05: Engine — NPC Roster

**File:** `ccya/engine/npc_roster.py`

**What:**
- In `_compute_npc_score` (lines 14-38):
  - Remove `aliases = raw.get("aliases") or []` (line 19).
  - Remove alias-based unnamed check (lines 20-21: `if name and aliases and name.lower().strip() in {...}`).
  - Replace with: `if name and not _is_named(name): return 0`.
- Add `_is_named` function at module level.

**Why:** D3 — Replace alias-based unnamed detection with proper-name heuristic.

**Validation:** `_compute_npc_score` no longer references `aliases`. Uses `_is_named` for unnamed check.

---

## Phase 06: Prompts

### extract_scene_system.j2

**What:**
- Remove `aliases` from output schema JSON (line 11): remove `"aliases": ["..."]` from the example.
- Remove `"aliases": ["alias1"]` from field rules (line 65).
- Remove `aliases` from "Durable identity updates" bullet (line 82): change to "Update `name`, `title`, `bio`, `motivation`, `fear`, `leverage`".
- Remove entire "Alias-first naming (MANDATORY)" section (lines 110-116).
- Replace with name/title guidance: "`name` must be a first name and a surname (at least two words, no titles/prefixes/descriptors). `title` is for honorifics, roles, status descriptors."
- Remove "Promotion to named" logic (line 122).
- Remove group NPC rules (lines 102-108, 123-125).
- Remove "Unnamed NPCs (descriptive label in `name` + same string in `aliases`...)" references (lines 121, 91).
- Strengthen unnamed detection guidance: "An NPC is unnamed if their `name` does not look like a proper name — specifically, it must have at least two words with the first and last words capitalized (e.g., 'John Smith'). Everything else is unnamed."
- Remove ambient presence requirement (line 188: "There MUST always be at least 1 NPC with `presence: 'present'`...").
- Add explicit deduplication instructions: strengthen existing section at line 178.
- Add scene NPC count guidance: "Keep scenes to 6-8 NPCs total. Confrontational scenes should have at most 3."
- Remove "Group NPC IDs" critical section (lines 102-108).
- Remove "Group NPC bio" guidance (line 125).
- Remove "Unnamed ambient characters" note (line 155).

### generate_seed_system.j2

**What:**
- Remove `aliases` from schema in TypeScript definition (line 36): the schema already doesn't have aliases — verify.
- Remove "Unnamed NPCs (descriptive label in `name` + same string in `aliases`...)" guidance (line 91).
- Remove group NPC guidance (lines 97-101).
- Strengthen name guidance: "`name` must be a first name and a surname (at least two words, no titles/prefixes/descriptors)."
- Strengthen title guidance: "Titles, roles, descriptors go in `title` field."
- Add scene NPC count guidance.
- Remove "Group NPC ID rule" (line 99).
- Remove "Group NPC bio" guidance (line 101).

### narrate_system.j2

**What:**
- Remove "NPC QUANTITY RULE" (line 75).
- Remove "NEW GROUPS" guidance (line 61).
- Remove "REINTRODUCING GROUPS" guidance (line 63).
- Simplify "NPC NAMING" guidance (line 80): remove "Descriptive labels are aliases" — replace with proper-name guidance.
- Add scene NPC count guidance: "Keep scenes to 6-8 NPCs total. Reference existing NPCs by name, don't introduce duplicates."
- Add guidance: "If an NPC is already in the compendium, reference them by their existing name. Do not introduce them again as a new character."

**Why:** D1 + D2 + D4 + D7 + D8 — Remove all aliases, group NPC, and ambient presence references. Add dedup and count guidance. Strengthen name/title separation.

**Validation:** All three prompt templates no longer reference `aliases` (except inventory aliases in extract_state_system.j2 which is unrelated). No group NPC guidance. No ambient presence requirement. Proper-name heuristic guidance present.

---

## Phase 07: Server + Templates

### routes.py

**File:** `ccya/server/routes.py`

**What:** Remove `alias` fallback in `display_name` logic (lines 545-549):
- Change from: `entry.get("name") or entry.get("alias") or (entry.get("aliases", [])[0] if entry.get("aliases") else key)`
- To: `entry.get("name") or entry.get("title") or key`

### _state_left.html

**File:** `templates/_state_left.html`

**What:**
- Remove `{% set _aliases = ... %}` (line 154).
- Remove `entry.aliases` fallback in compendium-line (line 156: change `entry.aliases[0] if entry.aliases else nid` to just `nid`).
- Remove "Previously known as" display (line 159).

**Why:** D1 — Remove all aliases references from server and templates.

**Validation:** `display_name` logic no longer references `alias` or `aliases`. Template no longer renders aliases.

---

## Phase 08: Exports + Docs

### state/__init__.py

**File:** `ccya/state/__init__.py`

**What:** Remove `build_npc_alias_map` from imports (line 27) and `__all__` (line 35).

### Docs

**What:** Update `docs/architecture/` docs that reference aliases, group NPCs, or the old unnamed detection. Update `docs/repomap.md` to reflect new `_is_named` function and removed functions.

**Why:** Clean up exports. Keep docs accurate.

**Validation:** `build_npc_alias_map` is no longer exported. Docs reflect the new heuristic.
