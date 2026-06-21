# Outer Rim — Full Eval Report (Updated 2026-06-21)

**Save:** `saves/the-outer-rim--after-unification-2026-06-20/`
**Turns:** 18→34 (save grew during investigation) | **Pack:** space-western (seeded) | **PC:** Jonathan Scott
**Date:** 2026-06-21 | **Re-investigation:** 2026-06-21 (second pass, 34-turn save)

---

## Focused Findings — Current Status

### 1. Narration in third person instead of second person

**Status: OPEN — targeted for fix.**
The narrator prompt says "Second person." but the LLM consistently outputs third person (`"Jonathan Scott unlatchs..."` instead of `"You unlatch..."`). No pack-level `narrator_rules` exist in space-western to override it.

**Trialed fix (reverted — too verbose):** Added a `BINDING RULE` section with examples. Reverted per instruction — keep it terse. Final fix: just strengthen the single-line directive, ensure no conflicting instructions in the prompt.

### 2. Unnamed characters' revealed names do not supersede alias

**Status: DEFERRED — no engine-level fix.**
The LLM creates new entries (`kaelen_vance`, `jory_miller`) instead of updating the `two_scavengers` group entry. The prompt already tells the LLM to do the right thing. The Python dedup (`_dedup_compendium_update`, `apply_npc_scene_management`) can't match "Kaelen Vance" to "Two scavengers" by any existing rule.

**Trialed fix (reverted — too complex):** Added `_find_group_for_individual()` — fuzzy group→individual merge. Reverted per instruction. The fallback plan is to eliminate plural NPC groups from seeds entirely if alias-first naming can't be made reliable.

### 3. NPC turn vs seed out of line — needs parity

**Status: CLOSED — no action needed.** This was working well in the original eval. The user noted it as deferred during the review.

### 4. Scene not sending storytell potential beats as expected

**Status: CLOSED — deferred per user.** "Should be fixed soon, no worries."

### 5. Names in narration not capitalized

**Status: CLOSED — not reproducible.** "Defer/call it a one-off."

### 6. Chronical tab on mobile seems broken

**Status: CLOSED — fixed itself.**

### 7. EXTRACTION_COERCION_FAILED: arc_resolve empty dict (T3)

**Status: OPEN — fix approved.**
Confirmed: LLM emits `arc_resolve: {}` (empty dict). Pydantic `ArcResolution` requires `resolution`, `visible_goal`, `goal_context` so `{}` fails validation before the existing `_nullify_empty_arc_resolve` after-validator runs.

**Fix applied:** Added `arc_resolve` nullification in `_coerce_scene_json()` (extraction/utils.py) — strips empty dict before Pydantic sees it, matching the existing `thread_add` empty-dict pattern. User approved this approach.

### 8. Threads not rightly assigned types

**Status: OPEN — fix approach changed.**
Confirmed: storyteller output missing `type` on `thread_add`/`thread_update`. The prompt says "set `type` to match the thread's semantic role" but the LLM treats it as optional.

**Trialed fix (reverted — too complex):** Added `_infer_thread_types` model_validator with keyword matching. Reverted per instruction. **New approach:** Make `type` a required field in the prompt guidance. The model already constrains it to the 4 valid types. Tersely clarify that every thread MUST have a type, and it must be one of the four.

### 9. Choices are removed on refresh

**Status: CLOSED — deferred per user.** "Defer and drop for now."

### 10. Present NPCs lost on location changes

**Status: CLOSED — dropped per user.**
Save data confirmed the issue: `apply_delta()` in `delta_builder.py:228-234` demotes all `presence: "present"` NPCs to `"nearby"` on location change. The scene extractor then only re-promotes NPCs explicitly mentioned in narration, creating a 1-turn gap.

**Root cause found.** User decided to rework this separately — no changes in this pass.

**`chapter_end` investigation:** The `chapter_end` field on `StorytellerResult` (`bool`, default `False`) is logged and recorded as `last_chapter_end_turn` in meta when the LLM sets it. It has no behavioral effect today — the engine does NOT reset arc state on chapter_end. It's a signal for future use (UI markers, pacing heuristics).

### 11. Arc resolution far too common

**Status: OPEN — targeted for prompt fix.**
Confirmed: arc_resolve fires at T4, T6, T15, T31 — all with the same visible goal "Establish a reliable smuggling route through the Millerport blockade." The prompt says target 8-15 turns per arc and warns against no-op goal updates. The LLM ignores both.

**Root cause:** The LLM can't update the visible_goal without closing/reopening the arc, so it uses arc_resolve to signal "this mini-arc is done." The fix is improved prompt guidance: emphasize arc_resolve should be reserved for major chapter endings, not minor beats. One or two examples, terse.

### 13. Nameless NPCs still getting personalities

**Status: OPEN — targeted for prompt + Python guard fix.**
The `[]` display for unnamed NPCs' personality in the prompt comes from the template rendering. The seed defines personalities for named NPCs, but the scene extractor occasionally emits entries without personality for named NPCs, or with empty personality for unnamed ones.

**Fix plan:**
1. Scene extractor prompt: clarify that unnamed NPCs (name matches alias) get NO personality fields — bio only.
2. Python guard in `apply_npc_scene_management`: block personality assignment on entries whose `name` matches an alias (i.e., unnamed NPCs). Also block non-bio fields (motivation, fear, leverage, bond) on unnamed entries. This already partially exists but needs strengthening.

### 14. Pacing — pursuit arc too long

**Status: CLOSED — separate design exists.** User has a design to fix this. Follow-up separately.

### 15. Beats

**Status: OPEN — targeted for fix.**
Beats are vague, driver matching is broken, personality is a weak fallback type.

**Fix applied (2026-06-21):**
- Removed `personality` from allowed beat types in `extract_scene_system.j2` — it describes *how* an NPC acts, not *why*. Narrator already has this info. Null beat is always valid.
- Added type-specific effect templates: motivation/fear/leverage/bond each get concrete behavioral pressure descriptions.
- Added "observable behavioral pressure, not internal state" rule for effects.
- Added `storytell_system.j2` beat flavor mapping: each type gets concrete narrative direction (motivation=pursues goal, fear=avoids something, leverage=exercises advantage, bond=history impacts present).
- Combined rule + agency rule into single "Action rule": every beat must show NPC/world taking action, never "nothing happens" or "atmosphere is tense."
- Added "if no psychological pressure relevant, emit null" to storytell.

---

## Additional Findings (from original eval, not re-evaluated)

- **Thread proliferation (14 created, 13 pending):** Not re-investigated in this pass. Noted as a secondary concern.
- **Arc goal updates are no-ops:** Covered by finding #11.
- **Sanitizer runs sparse:** Not re-investigated.
- **GM beat TTL accumulation:** The `recent_beats` TTL and cap (5 entries) are working correctly in the 34-turn save.

---

## Changes Made This Session

### Applied (approved by user):
- `ccya/engine/extraction/utils.py` — `_coerce_scene_json`: strip empty `arc_resolve: {}` before Pydantic validation. Prevents EXTRACTION_COERCION_FAILED.
- `ccya/prompts/extract_scene_system.j2` — removed `personality` from allowed types, added type-specific effect templates, "observable behavioral pressure" rule, unnamed NPC guard.
- `ccya/prompts/storytell_system.j2` — added beat flavor mapping table, "Action rule" combining rule + agency rule, "emit null if no pressure relevant."
- `ccya/state/npcs.py` — `_is_unnamed` guard blocking motivation/fear/leverage/bond/personality on unnamed NPCs (placed before assignment block).
- `ccya/engine/extraction/context.py` — `_filter_unnamed_personality()`: strips personality from unnamed NPC candidates.
- `docs/architecture/step2c-storytell.md` — updated `type` field documentation.
- `docs/architecture/step2a-scene.md` — updated unnamed NPC guard documentation.

### Reverted (per user instruction):
- `ccya/state/npcs.py` — group→individual merge logic (`_find_group_for_individual`, `_is_group_npc`). Too complex, deferring alias-first naming issue.
- `ccya/models/extraction.py` — thread type inference validator. Too complex, replacing with prompt-only fix.
- `ccya/prompts/narrate_system.j2` — verbose second-person examples. Replacing with terse directive clarification.

### Pending (plan follows):
- #1: Terse second-person directive in narrate_system.j2
- #8: Clarify thread `type` as required in storytell_system.j2
- #11: Tighter arc_resolve guidance with example in storytell_system.j2
- #13: Python guard blocking personality on unnamed NPCs + scene extractor prompt clarification
