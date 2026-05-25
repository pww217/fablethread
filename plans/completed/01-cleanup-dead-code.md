# Phase 01 — Cleanup Dead Code and Unused Features

## Status
`completed`

## Phases

3 phases: (01) remove dead code, unused features, obsolete config/state keys; (02) add ArcThread.key deduplication + ARC_UPDATE exposure for optional key field validation against auto-merge; (03) overhaul pacing system to collapse location_age/combat_age into scene_age with effective_scene_age combat boost, new Scene Pressure/Imperative directives using age thresholds instead of combat checks, pending_gm_beat carryover fix, consecutive_pressure_turns counter.

## Issue
The codebase contains dead features and unused config/state keys that consume tokens in prompts without any effect: `recently_left` NPC tracking (no downstream consumers), JUST_LEFT enum value with full processing pipeline but no callers, `_inject_location_pressure()` function never invoked anywhere, Location Pressure/Imperative directives defined in narrate_system.j2 but not emitted by any pacing logic, nearby locations section in narrate_user.j2 guarded on `world_locations` which is always empty (no packs define any locations). These dead features create confusion for executors and waste prompt tokens.

## Solution
Remove all dead code paths before adding new functionality to avoid executors tripping over unused references when modifying related functions or prompts. This phase removes: recently_left population/decay/JUST_LEFT processing pipeline, _inject_location_pressure() function (confirmed 0 call sites), Location Pressure/Imperative directive definitions from narrate_system.j2, nearby locations section from narrate_user.j2, world_locations parameter pass-through in narrate.py, obsolete config fields location_pressure_at/location_imperative_at. No new functionality is added — only removal of dead code to create a clean baseline for subsequent phases.

## Firm decisions
1. This phase removes ONLY dead code and unused features. No new logic, no config additions, no pacing rewrites (those are Phase 03).
2. `_inject_location_pressure()` in turn.py is confirmed dead — grep found only the function definition itself with zero call sites anywhere in the codebase.
3. `world_locations` parameter pass-through to narrate templates always carries empty list because no packs define any locations (`ctx.packing.get("locations", [])` returns `{}`). The nearby locations section in narrate_user.j2 is therefore never rendered even when guards pass.
4. Location Pressure and Location Imperative directives are defined as bullet points under `<<<DIRECTIVES_START>>>`/`<<<DIRECTIVES_END>>>` in narrate_system.j2 but no pacing logic emits them — they consume prompt tokens for nothing.
5. Tests temporarily removed during refactor per AGENTS.md; test references to JUST_LEFT/recently_left noted below but not modified as part of this phase.

## Non-goals
- Adding ArcThread.key deduplication (Phase 02)
- Rewriting pacing directives or adding Scene Pressure/Imperative definitions (Phase 03)
- Removing pending_gm_beat carryover fix logic (Phase 03)
- Changing any config field defaults or adding new config fields beyond removal of obsolete ones
- Modifying tests

## Risks, Ambiguities, and Blockers
1. **Test breakage:** `tests/test_schema.py:231` references `NpcPresence.JUST_LEFT` which will fail when the enum value is removed. Per AGENTS.md ("Tests are temporarily removed during refactor"), this is acceptable — tests will need updating when re-enabled but not as part of Phase 01.
2. **Test fixture stale data:** `tests/conftest.py:218-219` includes `"recently_left": []` and `"recently_left_turns": 2` in the scene fixture, plus line 221 has `"location_entered_turn": 1` which will be removed in Phase 03. These are inert test data that won't cause failures but will become stale — acceptable to leave until tests re-enable.
3. **Config field removal safety:** Removing `location_pressure_at` and `location_imperative_at` from EngineConfig is safe because `_inject_location_pressure()` (the only function that reads them) is dead code with zero call sites. No other config consumer references these fields.

## Implementation — Phase 01: Cleanup Dead Code and Unused Features

### Context files to load
- `/Users/pwilson/Repos/ccya/ccya/state/npcs.py`
- `/Users/pwilson/Repos/ccya/ccya/engine/turn.py`
- `/Users/pwilson/Repos/ccya/ccya/engine/extraction.py`
- `/Users/pwilson/Repos/ccya/ccya/engine/npc_roster.py`
- `/Users/pwilson/Repos/ccya/ccya/models.py` (NpcPresence enum)
- `/Users/pwilson/Repos/ccya/ccya/engine/narrate.py`
- `/Users/pwilson/Repos/ccya/ccya/prompts/narrate_user.j2`
- `/Users/pwilson/Repos/ccya/ccya/prompts/narrate_system.j2`
- `/Users/pwilson/Repos/ccya/ccya/prompts/sections/_npc_roster.j2`
- `/Users/pwilson/Repos/ccya/ccya/engine/config.py`

### Detailed steps

#### Step 1.1 — Remove recently_left population logic from scene state computation

**File:** `ccya/state/npcs.py`

**What:** Delete the block at lines ~229-241 that computes left_ids, builds the recently_left list from compendium NPC data, and sets scene["recently_left"] + scene.setdefault("recently_left_turns", 2). This is the sole producer of recently_left in scene state.

**Why:** The recently_left feature has no downstream consumers — it's populated but never meaningfully used (JUST_LEFT handling will be removed in Step 1.3, decay logic deleted in Step 1.2). Removing the producer eliminates an entire unused data pipeline.

**Validation:** `rg -n "recently_left" ccya/state/npcs.py` returns no matches after edit.

#### Step 1.2 — Remove recently_left decay block from turn processing

**File:** `ccya/engine/turn.py`

**What:** Delete the block at lines ~1422-1430 that decays scene.recently_left_turns counter and clears scene["recently_left"] when it reaches 0. This is engine-side decay logic for an unused feature.

**Why:** The recently_left data will no longer exist after Step 1.1 removes its producer, so the decay block has nothing to operate on. Removing both producer and consumer together prevents orphaned state mutations.

**Validation:** `rg -n "recently_left" ccya/engine/turn.py` returns zero matches for this block's content (bio collection removal in Step 1.4 will handle remaining references).

#### Step 1.3 — Remove recently_left parameter, processing block, and JUST_LEFT ordering from npc_roster.py

**File:** `ccya/engine/npc_roster.py`

**What:** Three changes:
- Delete the `recently_left` parameter from build_npc_roster() function signature (line ~17)
- Delete the entire recently_left processing loop at lines ~40-55 that iterates over recently_left NPCs and adds them to seen dict with NpcPresence.JUST_LEFT value
- Remove JUST_LEFT entry from ordering dict `{NpcPresence.PRESENT.value: 0, NpcPresence.JUST_LEFT.value: 1, ...}` — delete the line containing `NpcPresence.JUST_LEFT.value` (line ~77)

**Why:** build_npc_roster receives recently_left as a parameter but nobody meaningful uses it. The JUST_LEFT presence value is only assigned in this deleted block and has no downstream consumers beyond ordering NPCs by presence tier. Removing all three together eliminates the NPC roster integration point for the dead feature.

**Validation:** `rg -n "recently_left|JUST_LEFT" ccya/engine/npc_roster.py` returns zero matches after edit.

#### Step 1.4 — Remove JUST_LEFT enum value from NpcPresence in models.py

**File:** `ccya/models.py`

**What:** Delete the line containing `JUST_LEFT = "just_left"` from the NpcPresence enum (line ~24). The enum will have PRESENT, NEARBY, KNOWN remaining.

**Why:** JUST_LEFT is only assigned in Step 1.3's deleted processing block and has no other consumers. Removing it makes the type system enforce that no new code can reference this presence value.

**Validation:** `rg -n "JUST_LEFT" ccya/models.py` returns zero matches after edit.

#### Step 1.5 — Remove _inject_location_pressure function from turn.py

**File:** `ccya/engine/turn.py`

**What:** Delete the entire `_inject_location_pressure()` function definition at lines ~702-725. This function takes ages dict, existing_pressure list, and location staleness config thresholds to inject Location Pressure directives into pacing context — but is never called anywhere in the codebase (confirmed 1 grep match = only the def line itself).

**Why:** Dead function with zero call sites. It reads config fields that will be removed in Step 1.9 (`location_pressure_at`, `location_imperative_at`). Removing it eliminates both the dead code and makes those config field removals safe (no hidden consumers).

**Validation:** `rg -n "_inject_location_pressure" ccya/engine/turn.py` returns zero matches after edit.

#### Step 1.6 — Remove recently_left bio collection from turn.py compendium bios section

**File:** `ccya/engine/turn.py`

**What:** Delete the block at lines ~933-944 that iterates over state["scene"]["recently_left"] to collect NPC compendium bios for the narrate prompt. Update the comment above from "Compendium bios for present + recently_left NPCs (Phase 1)" to just reference present NPCs.

**Why:** The recently_left list will no longer exist after Step 1.1 removes its producer, so this bio collection loop has nothing to iterate over and produces empty results. Removing it eliminates dead code that reads from non-existent state.

**Validation:** `rg -n "recently_left" ccya/engine/turn.py` returns zero matches for the bio section content after edit.

#### Step 1.7 — Remove recently_left parameter from narrate() call in turn.py

**File:** `ccya/engine/turn.py`

**What:** Two changes:
- Delete the line passing `recently_left=(state.get("scene") or {}).get("recently_left", [])` to the narrate() function call (~line 995)
- Remove the `recently_left=` argument from the build_npc_roster() call within turn.py's narration setup (~line 1002). The remaining arguments (present_npcs, known_npcs) stay.

**Why:** These are the two call sites that pass recently_left data into narrate/npc_roster functions. Removing them severs the last connections to the dead feature from the engine side. After Step 1.3 removes the parameter from build_npc_roster's signature and Step 2.1 removes it from narrate's signature, these calls will match the new function contracts.

**Validation:** `rg -n "recently_left" ccya/engine/turn.py` returns zero matches after edit (all references removed).

#### Step 1.8 — Remove recently_left from build_npc_roster() call in extraction.py

**File:** `ccya/engine/extraction.py`

**What:** Delete the `recently_left=[]` argument from the `build_npc_roster()` call at line ~350. The remaining arguments (`present_npcs=extraction_ctx.present_npcs_this_turn`, `known_npcs=_known_characters_for_extract(state, compact=True)`) stay. Line 347-351 should become a two-line call with only the two required positional keyword args.

**Why:** Step 1.3 removes the `recently_left` parameter from build_npc_roster()'s signature. This is the third caller (besides turn.py and narrate.py) that will cause TypeError ("unexpected keyword argument 'recently_left'") if not updated. The call passes an empty list anyway (`[]`) so removing it has no functional impact — extraction.py's storytell step doesn't need recently_left NPC data for its prompt.

**Validation:** `rg -n "recently_left" ccya/engine/extraction.py` returns zero matches after edit (both the call site and cycle detection block in Step 1.9 will be removed).

#### Step 1.9 — Remove dead NPC cycle detection logic using recently_left in extraction.py

**File:** `ccya/engine/extraction.py`

**What:** Delete lines ~119-127 which build a set of recently_left IDs from scene state and use it to allow legitimate departures through the remove/add cycle check. The block starts with `recently_left = {` at line 119 and ends after `allowed = cycle_ids & recently_left` at line 126 (the `dropped` computation on lines 127-138 should be re-indented to sit directly under the `if cycle_ids:` guard, or deleted entirely if it only serves the recently_left optimization).

**Why:** After Step 1.1 removes scene["recently_left"] population from npcs.py, this block will always get an empty set and become inert dead logic. The NPC cycle detection optimization (allowing legitimate departures to bypass remove/add cycle rejection) has no value when recently_left is never populated. Removing it eliminates orphaned code that reads non-existent state data.

**Validation:** `rg -n "recently_left" ccya/engine/extraction.py` returns zero matches after edit.

#### Step 1.10 — Update _npc_roster.j2 JUST_LEFT references

**File:** `ccya/prompts/sections/_npc_roster.j2`

**What:** Two changes:
- Line ~2 comment: change "ordered PRESENT → JUST_LEFT → KNOWN" to "ordered PRESENT → NEARBY → KNOWN" (matching the new 3-entry ordering dict from Step 1.3)
- Delete line ~15 entirely: `{%- if n.presence == 'just_left' %} — Do not write dialogue or new action for this character this turn.{% endif %}`

**Why:** JUST_LEFT presence value will be removed from NpcPresence enum (Step 1.4) and build_npc_roster() will no longer produce `presence == 'just_left'` entries (Step 1.3). The comment listing the ordering becomes stale, and the conditional block is dead template code that always evaluates to false — it wastes tokens for nothing.

**Validation:** `rg -n "JUST_LEFT|just_left" ccya/prompts/sections/_npc_roster.j2` returns zero matches after edit.

#### Step 1.11 — Remove recently_left and world_locations parameters from _narrate_messages() in narrate.py

**File:** `ccya/engine/narrate.py`

**What:** Four changes:
- Delete the `recently_left` parameter from `_narrate_messages()` function signature (~line 31)
- Delete the `world_locations` parameter from the same function signature (~line 42)
- Remove the `recently_left=` argument from the build_npc_roster() call inside narrate.py (~line 52). The remaining arguments (present_npcs, known_npcs) stay.
- Update the optional variables comment block around lines ~89-91 to remove references to `recently_left` and `world_locations` from the listed optional context vars

**Why:** These parameters receive data that is never meaningfully consumed — recently_left has no downstream template consumers, world_locations always carries an empty list. Removing them cleans up function signatures to match the new parameter-less calls from Step 1.7 in turn.py. Also removes `recently_left` and `world_locations` entries from user_ctx dict (~lines 103 and 116).

**Validation:** `rg -n "recently_left|world_locations" ccya/engine/narrate.py` returns zero matches after edit.

#### Step 1.12 — Remove nearby locations section from narrate_user.j2

**File:** `ccya/prompts/narrate_user.j2`

**What:** Delete the block at lines ~44-48: the Jinja guard `{% if world_locations and ages and ages.get('location_age', 0) >= 3 -%}`, the section header "### Nearby Locations", the for-loop rendering each location, and the closing `{% endif -%}`. The next section ("## Prior Turns (Compacted)") follows immediately after.

**Why:** This section is guarded on `world_locations` which always carries an empty list because no packs define any locations (`ctx.packing.get("locations", [])` returns `{}`). Even when location_age >= 3, the for-loop renders nothing — the section exists only to consume prompt tokens. Removing it eliminates dead template logic that never produces output.

**Validation:** `rg -n "world_locations|Nearby Locations" ccya/prompts/narrate_user.j2` returns zero matches after edit.

#### Step 1.13 — Remove JUST_LEFT text from NPC RE-USE directive in narrate_system.j2

**File:** `ccya/prompts/narrate_system.j2`

**What:** Edit the NPC RE-USE paragraph (~line 50) to remove the sentence about JUST_LEFT ("JUST_LEFT means they departed this turn — do not write new dialogue for them, but you may briefly acknowledge their exit."). Keep the PRESENT and KNOWN descriptions intact. The directive should read: "PRESENT means they are in the room. KNOWN means they are not in the scene but could plausibly arrive."

**Why:** JUST_LEFT presence value will be removed from NpcPresence enum (Step 1.4). This instruction to the storyteller references a non-existent state and wastes prompt tokens on guidance for handling data that no longer exists.

**Validation:** `rg -n "JUST_LEFT" ccya/prompts/narrate_system.j2` returns zero matches after edit.

#### Step 1.14 — Remove Location Pressure directive from narrate_system.j2

**File:** `ccya/prompts/narrate_system.j2`

**What:** Delete the full bullet point for Location Pressure under the directives section (~line 111). This is the line starting with `- **Location Pressure**` that instructs the storyteller to wind down when players have been in a location 3+ turns.

**Why:** No pacing logic emits this directive — it's defined as an instruction to the storyteller but never triggered by any engine computation. It consumes prompt tokens for nothing and will be replaced by Scene Pressure/Imperative definitions in Phase 03 (different concept, different trigger mechanism). Removing dead directives keeps prompts lean.

**Validation:** `rg -n "Location Pressure" ccya/prompts/narrate_system.j2` returns zero matches after edit.

#### Step 1.15 — Remove Location Imperative directive from narrate_system.j2

**File:** `ccya/prompts/narrate_system.j2`

**What:** Delete the full bullet point for Location Imperative under the directives section (~line 110). This is the line starting with `- **Location Imperative**` that instructs the storyteller to force movement when players have been in a location 5+ turns.

**Why:** Same as Step 1.14 — no pacing logic emits this directive, it's dead template text consuming tokens without effect. Will be replaced by Scene Imperative definition in Phase 03 with different trigger mechanism (scene_age thresholds instead of location staleness).

**Validation:** `rg -n "Location Imperative" ccya/prompts/narrate_system.j2` returns zero matches after edit.

#### Step 1.16 — Remove obsolete config fields from EngineConfig and build_engine_config()

**File:** `ccya/engine/config.py`

**What:** Two changes:
- Delete the three lines (~98-100) containing the comment "# Location staleness thresholds (turns since last location change)" plus the two field definitions `location_pressure_at: int = 3` and `location_imperative_at: int = 5` from EngineConfig dataclass
- Delete the two parsing lines in build_engine_config() (~171-172) that construct these fields from game config dict

**Why:** These config fields were only consumed by `_inject_location_pressure()` which is deleted in Step 1.5 (confirmed zero call sites). Removing them eliminates dead config keys that consume memory and could confuse future executors into thinking they're active features. The field defaults (3/5) match the new scene_age thresholds proposed for Phase 03 but serve a completely different purpose — location staleness vs scene age, so no value preservation needed.

**Validation:** `rg -n "location_pressure_at|location_imperative_at" ccya/engine/config.py` returns zero matches after edit.

### Tests to write or update
Per AGENTS.md ("Tests are temporarily removed during refactor"), tests are skipped for this phase. The following test references will need updating when tests re-enable:
- `tests/test_schema.py:231` — uses `NpcPresence.JUST_LEFT`; will fail until changed to another enum value (e.g., PRESENT or KNOWN)
- `tests/conftest.py:218-219` — scene fixture includes `"recently_left": []` and `"recently_left_turns": 2`; inert data that won't cause failures but will become stale

### REPOMAP updates required
No structural changes to modules or public APIs. The following internal references change:
- `ccya/models.py`: NpcPresence enum shrinks from 4 values (PRESENT, JUST_LEFT, NEARBY, KNOWN) to 3 (PRESENT, NEARBY, KNOWN). REPOMAP should note removal of JUST_LEFT value if it documents the full enum.
- `ccya/engine/npc_roster.py`: build_npc_roster() signature changes from `(present_npcs, known_npcs, recently_left)` to `(present_npcs, known_npcs)`. Ordering dict shrinks from 4 entries to 3 (removes JUST_LEFT:1). REPOMAP should note the removed parameter if it documents function signatures.
- `ccya/engine/narrate.py`: `_narrate_messages()` signature changes from including `recently_left` and `world_locations` parameters to excluding both. REPOMAP should note these removals if documenting function signatures.
- `ccya/engine/extraction.py`: build_npc_roster() call at line ~350 no longer passes `recently_left=[]`; NPC cycle detection block using recently_left (lines 119-127) removed from `_validate_scene_npcs()` or equivalent validation helper. REPOMAP should note removal if it documents scene extraction internals.
- `ccya/prompts/sections/_npc_roster.j2`: Comment on line ~2 updated to reflect new ordering ("PRESENT → NEARBY → KNOWN"); dead conditional block for JUST_LEFT presence removed from line ~15. REPOMAP section documenting prompt templates should note removal of just_left handling if it references the full roster rendering logic.
- `ccya/prompts/narrate_system.j2`: JUST_LEFT sentence removed from NPC RE-USE paragraph (Step 1.13); Location Pressure bullet deleted (Step 1.14); Location Imperative bullet deleted (Step 1.15). REPOMAP should note removal of these three directive definitions and the NPC RE-USE text change if it documents narrator prompt structure.
- `ccya/prompts/narrate_user.j2`: "### Nearby Locations" section (lines 44-48) removed entirely — world_locations guard, section header, and for-loop deleted (Step 1.12). REPOMAP should note removal of this template section if it documents user prompt structure.
- `ccya/engine/config.py`: `location_pressure_at` and `location_imperative_at` fields removed from EngineConfig dataclass (old lines 99-100); corresponding build_engine_config mapping lines removed (old lines 171-172). REPOMAP should note removal of these config keys if it documents EngineConfig fields.
