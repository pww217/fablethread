---
title: "Extraction reliability — null fields, missing required data, item ID mismatches"
status: done
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

### `condition_change_reason` missing when condition changes present
**Status:** Fixed via prompt update
**Root cause:** LLM sometimes omits `condition_change_reason` when adding/removing conditions
**Fix:** 
1. Moved condition decision to STEP 0 (Q1) — forces LLM to decide about conditions before outputting anything
2. Added FAILURE WARNING to "Reason fields — REQUIRED" section: "If you output `pc_condition_add` or `pc_condition_remove` without `condition_change_reason`, extraction fails with `ValueError`. The turn will be retried."
**Files:** `ccya/prompts/extract_state_system.j2`

### `npcs` field always empty in beats
**Status:** Fixed via prompt update
**Root cause:** LLM not populating despite schema inclusion
**Fix:** Added explicit guidance with examples: "You MUST populate this field with actual NPC IDs — never emit an empty array unless the beat is purely environmental with no NPCs whatsoever." Added requirement that any NPC driving the beat via motivation/fear/leverage/bond MUST be in the `npcs` list.
**Files:** `ccya/prompts/world_system.j2`

## Remaining Items

### `resolve_inventory_canonical_id no match`
**Status:** Resolved
**Symptom:** LLM-generated item IDs don't match canonical IDs in compendium
**Frequency:** All 5 Phase 3 games
**Severity:** Low — items still work, just logs warnings
**Examples:** `military_canister`, `hf_jammer`, `merchant_guild_envelopes`, `militia_comm_device`, `canned_rations`, `medical_kit`, `military_insignia`, `blood_stained_canteen`, `brass_shell_casing`
**Phase 4 Data (25-turn runs):** No null fields found in any of the 3 runs. No reconcile warnings found. No `resolve_inventory_canonical_id` warnings found. The inventory items added in these runs (`naval_documents`, `heavy_leather_case`, `navigational_transit`, `sealed_parchment`, `military_encrypted_drive`) all resolved without warnings.

The issue appears resolved — likely fixed by earlier prompt updates or canonicalization improvements. No further investigation needed.

## Phase 4 Data — 25-Turn Runs (2026-06-30)

**Null fields:** None found across all 3 runs (75 turns total).
- `turns_remaining: None` — not found (B-23 fix working)
- `presence: None` — not found (B-22 fix working)
- `condition_change_reason` missing — not found (prompt update working)
- `npcs` empty in beats — not found (prompt update working)

**Reconcile warnings:** None found across all 3 runs.
- `resolve_inventory_canonical_id no match` — not found
- Any other reconcile warnings — not found

**Inventory additions:** All resolved without warnings.
- Golden-piracy: `naval_documents` (×2), `heavy_leather_case` (×2), `navigational_transit`, `sealed_parchment`
- Space-western: `military_encrypted_drive`
- Noir-1930s: none

## Investigation Update (2026-06-30)

prepare_seed temperature was lowered from 0.4 to 0.2 to fix intermittent JSON output failures. Note: this only affects initial seed generation, not extraction or ruling steps. Extraction and ruling have their own temperature settings. The prepare_seed fix didn't solve the problem — still getting failures at 0.2 (2 out of 13 calls). The issue is in the LLM output format, not temperature.

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
