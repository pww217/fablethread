---
title: "Extraction reliability — null fields, missing required data, item ID mismatches"
status: new
urgency: 2
size: medium
created: 2026-06-29
ticket_id: B-24
labels: [extraction, validation, reliability]
superseded:
  - roadmap/bugs/B-22-scene-extractor-omits-presence-field-new-npc-entries.md
  - roadmap/bugs/B-23-conditions-with-null-turns_remaining-trigger-warning.md
---

## Description

LLM extraction steps produce invalid or incomplete state data across multiple fields. Some issues are fixed, others remain.

## Fixed Items (Reference Only)

### `turns_remaining: None` on conditions
**Status:** Fixed
**Root cause:** Pydantic v2 accepts `null` from JSON and sets `None` instead of default `0`
**Fix:** Added `@field_validator("turns_remaining", mode="before")` to `Condition` and `ConditionAdd` models in `ccya/models/state.py` to coerce `None` → `0`
**Files:** `ccya/models/state.py`
**Reference:** B-23 (superseded by this ticket)

### `presence: None` on new NPC entries
**Status:** Fixed via prompt update
**Root cause:** LLM not following prompt instruction for new NPCs
**Fix:** Added explicit requirement to `ccya/prompts/extract_scene_system.j2` line 50: "Presence is REQUIRED for every NPC update — never omit it."
**Files:** `ccya/prompts/extract_scene_system.j2`
**Reference:** B-22 (superseded by this ticket)

### World prompt schema missing `npcs` field
**Status:** Fixed via prompt update
**Root cause:** `ccya/prompts/world_system.j2` schema didn't include `npcs` field
**Fix:** Added `"npcs": ["npc_id_1", "npc_id_2"]` to schema
**Files:** `ccya/prompts/world_system.j2`

## Remaining Items

### `condition_change_reason` missing when condition changes present
**Status:** Open
**Symptom:** `extract_state parse failed` with `ValueError: condition_change_reason is required when condition changes are present`
**Frequency:** Observed in golden-piracy and allied-ww2 runs during Phase 3
**Impact:** Retry succeeded (attempt 2/2), but indicates LLM output validation gap
**Root cause:** LLM sometimes omits `condition_change_reason` when adding/removing conditions
**Need to investigate:** Prompt guidance, validation in extraction pipeline

### `npcs` field always empty in beats
**Status:** Open
**Symptom:** World prompt schema includes `npcs` field but LLM always outputs `[]`
**Impact:** No functional impact yet — `npcs` field not used in ruling/narration phases
**Root cause:** LLM not populating despite schema inclusion
**Need to investigate:** Add explicit instruction to populate `npcs`, or defer until ruling/narration phases use the field

### `resolve_inventory_canonical_id no match`
**Status:** Open
**Symptom:** LLM-generated item IDs don't match canonical IDs in compendium
**Frequency:** All 5 Phase 3 games
**Severity:** Low — items still work, just logs warnings
**Examples:** `military_canister`, `hf_jammer`, `merchant_guild_envelopes`, `militia_comm_device`, `canned_rations`, `medical_kit`, `military_insignia`, `blood_stained_canteen`, `brass_shell_casing`
**Need to investigate:** Improve item ID canonicalization, strengthen prompt guidance for item naming

## Files to Review

- `ccya/models/state.py` — Condition and ConditionAdd models
- `ccya/prompts/extract_scene_system.j2` — NPC presence guidance
- `ccya/prompts/world_system.j2` — Beat schema with npcs field
- `ccya/engine/extraction/pipeline.py` — State extraction retry logic
- `ccya/engine/turn_state.py` — `_expire_conditions` function
- `ccya/state/delta_builder.py` — Condition application logic
