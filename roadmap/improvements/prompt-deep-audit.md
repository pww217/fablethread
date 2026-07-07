---
title: "Prompt audit — architecture alignment, variables, schema, edge cases"
status: implemented
type: improvement
urgency: 3
size: large
created: 2026-06-29
ticket_id: I-2
labels: [prompts, audit]
---

## Audit Summary (validated 2026-07-03)

Audit completed by rendering prompts from live eval save (`1434_space-western_25t`, turn 8). Each finding validated against actual template content and boundary models.

### Results by severity

**High impact — broken contracts / wasted tokens:**
1. Boundary models out of sync with templates — ~~`RulingBoundary`, `NarratorBoundary`, `SceneExtractBoundary`, `StateExtractBoundary`, `StorytellerBoundary`~~ **RESOLVED**: StorytellerBoundary cleaned up (dead fields removed, missing fields added), template contract mapping fixed (`storytell_user.j2` → `record_user.j2`).
2. ~~Dead fields in `StorytellerBoundary`~~ — **RESOLVED**: removed 8 dead fields (npc_roster, intent, pacing_context, allowed_beat_types, pending_beat, recent_beats, conditions, inventory).
3. ~~`bond` → `tie` rename~~ — **RESOLVED**: `world_system.j2:23` prose example fixed, `pack.py:43` CompendiumEntry field renamed to `tie`.

**Medium impact — confusing prompts / model failures:**
4. ~~Ruling schema examples show wrong defaults~~ — **RESOLVED**: `"impossible": false`, `"check.required": false`.
5. ~~`reason` format contradiction in ruling~~ — **RESOLVED**: field rules now specify connector guidance for both difficulty and impossibility.
6. Urgency escalation mismatch — prompt says 3 turns, engine auto-dormant at 8. **LEFT AS-IS**: Different contexts (LLM guidance vs engine default) — acceptable.
7. ~~`meta.turn` fallback shows "?"~~ — **RESOLVED**: changed to "—" (em dash).

**Low impact — style / verbosity:**
8. ~~"mandatory"/"CRITICAL" overuse, presence levels defined 3x, tense ambiguity.~~ — **RESOLVED**: CRITICAL reduced from 9× to 4× in record; presence levels consolidated into single section in Scene Extract.

### Resolved findings (this session)
- Scene Extract: presence levels consolidated into "How to use" section (~20 lines saved)
- Scene Extract: dedup rules merged into NPC ID rules (~15 lines saved)
- Record: CRITICAL reduced from 9× to 4×; thread ID rules consolidated from 5 variants to 1
- `bond` → `tie`: `world_system.j2:23` prose example + `pack.py:43` data key fixed
- Narrate: "Every sentence must advance" merged into Pacing section
- State Extract: narration authority collapsed to single "Grounding" section
- StorytellerBoundary: 8 dead fields removed, 3 missing fields would need engine updates
- Ruling: schema defaults fixed, reason connector guidance added to field rules
- Template contract: `storytell_user.j2` → `record_user.j2` mapping fixed
- Ruling: `meta.turn` fallback "?" → "—"

# I-2: Prompt Audit

## Goal

Audit every prompt pair in `ccya/prompts/` with a structured rubric applied to each pair. One pair at a time. No changes during audit — findings logged for review.

## Rubric (applied to every pair)

### A. Architecture alignment
- Does the prompt match what the architecture doc says it should do?
- Are there fields the doc says should be present but aren't?
- Are there fields present that the doc doesn't mention?
- Does the prompt implement the correct step in the pipeline?

### B. Variable completeness & rendering
- Every `{{ var }}` in the template has a corresponding field in the boundary model?
- Every field in the boundary model is actually used in the template?
- Fallbacks are sensible (defaults, empty checks)?
- Jinja syntax correct and idiomatic?
- Section includes receive all variables they need?

### C. Schema/output discipline
- Schema example matches what the field rules actually say?
- Output instructions are unambiguous about what to emit vs omit?
- No contradictions between "emit X" and "omit Y" in different sections?
- JSON validity in examples?

### D. Internal consistency
- No self-contradictions within the prompt itself?
- Terminology consistent (same field name, same enum values, same constraints)?
- Examples match the rules they're illustrating?
- Constraints don't conflict with each other?

### E. Duplication & verbosity
- Same rule stated in 2+ places?
- Sections that could be merged?
- Instructions that repeat what's obvious from the schema?
- Redundant warnings or emphasis?

### F. Edge cases & error conditions
- What happens when a field is empty/null?
- What happens when there are 0 NPCs / 0 threads / 0 items?
- Are there guardrails against common model failures?
- Are there instructions for what NOT to do when data is missing?

### G. User prompt completeness
- Does the user prompt give the system prompt everything it needs?
- Are there instructions in the system prompt that reference data not in the user prompt?
- Is the user prompt organized logically for the model to parse?
- Are there variables in the user prompt that the system prompt never uses?

---

## Todo per pair

```
1. Read architecture doc for this step
2. Read system prompt
3. Read user prompt
4. Read boundary model in context.py for this step
5. Read all section templates used by this user prompt
6. Dump rendered prompt from eval save (turn 5, allied-ww2)
7. Dump rendered prompt from different eval save for variety (turn 10, space-western)
8. Walk through every line of system prompt against rubric A-G
9. Walk through every line of user prompt against rubric A-G
10. Walk through every include against rubric A-G
11. Walk through rendered output against rubric A-G
12. Cross-reference with architecture doc for missing/extra behavior
13. Log findings in ticket under correct pair letter
14. Flag any fixes needed (user approves before changes)
```

---

## Ticket structure

### A. Ruling (step0-ruling)
**Files:** `ruling_system.j2`, `ruling_user.j2`, `context.py:RulingBoundary`
**Arch doc:** `docs/architecture/step0-ruling.md`

#### A.1 Architecture alignment
- System prompt correctly implements intent classification + dice check decision + impossibility + scene motion + beat selection
- User prompt provides all inputs the architecture doc specifies: PC, conditions, situation, scene, NPCs, urgent threads, beat candidates, inventory, recent turns, player input
- `selected_beat` is in the ruling schema and IS used by `ruling.py:117` (extracted separately from IntentEnvelope) — correct
- `scene_motion` maps to `IntentEnvelope.scene_motion` — correct
- Architecture doc says ruling outputs `IntentEnvelope` + `RulesOutcome`; ruling system prompt generates IntentEnvelope fields — correct
- **Gap:** `scene_phase` is passed to ruling context (`ruling.py:173`) but never used by ruling prompts. It's used by narrator and storytell, but ruling doesn't leverage it for beat selection or difficulty.

#### A.2 Variable completeness & rendering
- `RulingBoundary` declares: `pc`, `location`, `user_input`, `meta`, `npc_roster`, `recent_turns`, `inventory`, `scene_phase`, `urgent_threads`
- **Dead field in boundary model:** `scene_phase` (line 230) — never referenced in `ruling_user.j2`
- **Missing from boundary model:** `pc_situation`, `beat_candidates`, `allowed_beat_types` — injected in `ruling.py:69-71` but not in `RulingBoundary`
- **Dead template code:** `ruling_user.j2:33-36` (`allowed_beat_types` section) — variable never passed to template, `{% if %}` always falsy
- **Dead render variable:** `state` passed in `ruling.py:69` but never referenced in `ruling_user.j2`
- `_pc_header.j2` uses `pc.tagline or pc.concept` — `PlayerBlock.concept=None` always (context.py:43), so tagline is the only active path
- `_conditions.j2` references `show_age` and `turn_no` as optional — never passed in ruling context, so age display never renders (correct behavior)
- `_recent_turns.j2` renders `recent_turns[-1]` — matches `ruling.py:172` which passes `ctx.recent_turns[-1:]`

#### A.3 Schema/output discipline
- **Schema example shows `"impossible": true`** — misleading; should show `false` as the common/default case
- **Schema example shows `"scene_motion": "hold"`** — correct as default
- **Schema example shows `"selected_beat": 0`** — correct, but `selected_beat` is NOT part of `IntentEnvelope` model; it's parsed separately. Schema should clarify this is an extra field
- **Schema shows `check.required: true`** — should show `false` as the default (decision rule says default to false)
- **Schema shows `check.skill` and `check.difficulty` without null markers** — unclear when these are omitted vs set to empty string
- **`intent_verb` example list in field rules is incomplete:** lists `attack | persuade | sneak | hack | deceive | intimidate | climb | repair | recall | escape | negotiate` but ruling.py has no validation — model can output any string

#### A.4 Internal consistency
- **`reason` format contradiction:** Line 3 says "Structure: [Ruling] [connector] [Reason]" but impossibility examples (lines 27-31) just show `"Draw my sword" — sword not in inventory` without the `[Ruling]` prefix. Field rules line 81 repeats the [Ruling] structure. Unclear if examples are wrong or the general rule has exceptions.
- **`reason` 10-word cap stated 3 times:** lines 3, 81, and implied by examples. Redundant but not contradictory.
- **`trivial` difficulty says "Non-combat only" (line 36)** but no alternative guidance for combat checks that need a low-difficulty roll. Is `easy` the combat equivalent of `trivial`?
- **Beat selection says "2-3 candidate beats" (line 89)** but user prompt handles "No beat candidates prepared" (line 31). System prompt overstates certainty about beat availability.
- **`intent_verb` mappings (line 79):** `pick lock → sneak` — debatable. Picking a lock could reasonably be `dexterity` without being "sneak." Minor semantic issue.

#### A.5 Duplication & verbosity
- **`reason` 10-word cap repeated 3 times** (lines 3, 81, and field rules restate)
- **Decision rule section (lines 42-49)** duplicates architecture doc verbatim — acceptable for self-containment but borderline
- **Impossibility examples (lines 27-31)** are good concrete illustrations, not redundant
- **Scene motion definitions (lines 51-55)** are concise and necessary
- System prompt is ~95 lines — reasonable for the complexity

#### A.6 Edge cases & error conditions
- **Empty `npc_roster`:** Template handles with `{% if npc_roster %}` — correct
- **Empty `urgent_threads`:** Template handles with `{% if urgent_threads %}` — correct
- **Empty `beat_candidates`:** Template handles with else clause — correct
- **Empty `recent_turns`:** `_recent_turns.j2` handles with `{% if recent_turns %}` — correct
- **Empty `inventory`:** `_inventory.j2` renders "Nothing of note." — correct
- **Missing `pc.name`:** `_pc_header.j2` falls back to "Unnamed" — correct
- **Missing `location.name` and `location.id`:** Both checked with fallback to "Unknown" — correct
- **No guardrail against model outputting `scene_motion` as invalid value** — schema says `hold | advance | transition` but no explicit "must be one of these" language
- **No guardrail against `check.skill` being set when `check.required=false`** — field rules say "only when required=true" but no explicit prohibition

#### A.7 User prompt completeness
- **Missing context for `scene_motion` determination:** System prompt defines hold/advance/transition but user prompt doesn't provide scene context (e.g., "player is at exit" → suggests transition) to help the LLM decide
- **Missing context for beat selection:** Beat candidates are listed but no guidance on what makes a beat a "good fit" beyond "drives pacing"
- **Missing `scene_phase` context:** Even though `scene_phase` isn't in the template, the phase could help ruling (e.g., CLIMAX turns should favor advance/transition)
- **`meta.turn` fallback `'| default('?')`** — turn 0 would show "?", which is confusing. Should be `'| default(1)'` or similar
- **Player input section uses `=== PLAYER INPUT ===` delimiters** — good for model parsing, but empty input (turn 1 or auto-play) just shows empty between delimiters

#### A.8 Findings:
- [ ] **Schema example misleading:** Shows `"impossible": true` and `"check.required": true` as defaults when both default to `false`. Should flip to `false`/`false`. **VALIDATED: confirmed.** Models follow examples more than prose — this causes real output errors.
- [ ] **`reason` format contradiction:** General rule says `[Ruling] [connector] [Reason]` but impossibility examples omit `[Ruling]` prefix. Either fix examples or clarify exception. **VALIDATED: confirmed.**
- [ ] **Dead template code:** `ruling_user.j2:33-36` references `allowed_beat_types` which is never passed — section never renders. Remove or wire in. **INVALIDATED: `allowed_beat_types` IS rendered at line 33-36 and IS passed by ruling engine. Not dead.**
- [ ] **Dead boundary model field:** `RulingBoundary.scene_phase` never used in template. Remove or use for beat selection guidance. **VALIDATED: confirmed.**
- [ ] **Missing from boundary model:** `pc_situation`, `beat_candidates` injected outside boundary system. Add to `RulingBoundary` for type safety. **VALIDATED: confirmed.** `pc_situation`, `beat_candidates`, `allowed_beat_types` all used in template but not in boundary model.
- [ ] **Dead render variable:** `state` passed to ruling template but never referenced. Remove from `_ruling_messages()`. **VALIDATED: confirmed.**
- [ ] **`trivial` difficulty gap:** Marked "non-combat only" but no guidance on what to use for low-difficulty combat checks. **VALIDATED: confirmed.**
- [ ] **Beat selection guidance weak:** "Pick the best fit" is vague. What criteria should the ruling LLM use? Narrative relevance? Pacing? NPC involvement? **VALIDATED: confirmed.**
- [ ] **`meta.turn` fallback:** `'| default('?')` shows "?" for turn 0. Should use a numeric default. **VALIDATED: confirmed.**
- [ ] **`reason` 10-word cap stated 3 times:** Consolidate to single authoritative statement. **VALIDATED: confirmed.**
- [ ] **`intent_verb` example list:** Consider adding `steal`, `use`, `open`, `close`, `read`, `listen` for common non-combat actions. **VALIDATED: confirmed.**
- [ ] **System prompt overstates beat availability:** "2-3 candidate beats" when candidates may not exist. Change to "candidate beats (if any)". **VALIDATED: confirmed.**

### B. Narrate (step1-narrate)
**Files:** `narrate_system.j2`, `narrate_user.j2`, `context.py:NarratorBoundary`, `context.py:NarratorSystemBoundary`
**Arch doc:** `docs/architecture/step1-narrate.md`
**Includes:** `_pc_header.j2`, `_conditions.j2`, `_inventory.j2`, `_location.j2`, `_npc_roster.j2`, `_world_state.j2`, `_thread_list.j2`, `_recent_turns.j2`, `_arc.j2`

#### B.1 Architecture alignment
- System prompt correctly implements: prose narration, player input priority, inventory constraints, NPC counts, no repetition, fail-band outcomes, NPC behavior drivers (motivation/fear/leverage/personality/bond), style rules, pacing, curtain call, campaign arc steering, markdown rules, genre/world rules, banned words
- User prompt provides: PC header, conditions, inventory, location, npc_roster, world state, factions/name pool, scene context (threads, phase), prior history, recent turns, arc, rules outcome, player input, pending beat, pacing context — matches architecture doc inputs
- `pending_beat` comes from `pending_gm_beat` in state — correct
- `curtain_call` passed to template — correct
- `arc_hint_text` passed in user_ctx (narrate.py:107) but never used in narrate_user.j2 — dead field
- `arc_pressure_score` passed in user_ctx (narrate.py:106) but never used in template — dead field
- `ages` declared in `NarratorBoundary` (context.py:255) but never used in template — dead field

#### B.2 Variable completeness & rendering
- `NarratorBoundary` declares: `pc`, `current_objective`, `state`, `npc_roster`, `pacing_context`, `recent_turns`, `prior_history`, `rules_outcome`, `user_input`, `pending_beat`, `meta`, `ages`, `pc_allegiance`, `world_factions`, `npc_name_pool`, `resolved_arcs`
- **Dead field in boundary model:** `ages` (context.py:255) — never referenced in `narrate_user.j2`
- **Dead field in boundary model:** `resolved_arcs` (context.py:259) — never referenced in `narrate_user.j2`
- **Dead render variables:** `arc_hint_text`, `arc_pressure_score` passed in `narrate.py:106-107` but never referenced in `narrate_user.j2`
- `state` dict covers `state.location`, `state.inventory`, `state.scene.world_state` accessed by includes — correct
- `current_objective` used in `_arc.j2` include — correct
- `state.long_term_objective` used as fallback for threads (line 35) — correct
- `state.scene.scene_phase` used on line 39 — correct
- `npc_roster` rendered via `_npc_roster.j2` — correct
- `rules_outcome` rendered on lines 55-71 — correct
- `pending_beat` rendered on lines 77-79 — correct
- `pacing_context` rendered on lines 80-83 — correct
- `meta.turn` used on line 54 — correct
- `pc_allegiance` used on line 18 — correct
- `_thread_list.j2` uses `turn_no` — available from user_ctx
- `_recent_turns.j2` uses `recent_turns` — available from user_ctx
- `_npc_roster.j2` uses `turn_no` — available from user_ctx

#### B.3 Schema/output discipline
- System prompt emphasizes "Output prose only — never list choices, never speak as the game" (line 1) — clear
- System prompt emphasizes "Second person only" (line 1) — clear
- Style rules are specific: "Every sentence must advance" (line 58), "One simile per turn maximum" (line 61), "No sensory templates" (line 62)
- Banned words section (line 107) is clear and actionable
- Fail-band outcomes (lines 29-33) are explicit about what NOT to do on FAIL
- No schema example to validate — this is prose generation, not structured output. Correct.

#### B.4 Internal consistency
- **Tense contradiction:** Line 1 says "Default terse — expand length only when complexity demands it" and "If the genre tone section below specifies a tense, use it; otherwise use past tense." But line 1 also says "Second person only" — second person is typically present tense. Unclear if genre tone overrides the "default past tense" rule or if past tense applies to second person narration.
- **Inventory constraint stated 3 times:** Lines 9 ("condition table and inventory table are authoritative"), 17 ("Items have proper names — use them as given"), 19 ("Inventory is a hard constraint"). Lines 9 and 19 are very similar.
- **"Player input is truth" vs "pragmatic interpretation":** Line 5 says "Never substitute a different action" but line 68 says "infer their intent and narrate a reasonable attempt" when action is unclear. These are complementary (edge case handling) but could conflict if the model interprets "unclear" differently.
- **NPC naming vs new character intro:** Line 54 says "Every NPC must be referred to by their exact proper name" but line 39 says "When introducing a new character, describe their appearance." New characters don't have proper names yet — minor tension.
- **"Each beat must advance" (line 72) and "Every sentence must advance" (line 58):** Overlapping emphasis.

#### B.5 Duplication & verbosity
- **System prompt ~107 lines:** Some sections could be tighter.
- **Inventory constraint stated 3 times:** Lines 9, 17, 19. Lines 9 and 19 are nearly identical.
- **"Every sentence must advance" / "Each beat must advance":** Lines 58 and 72. Consolidate.
- **NPC behavior drivers (lines 41-48):** Good content but overlaps with NPC section opening (line 37 "The scene extractor will capture these into the character's compendium bio" — not relevant to narration).
- **Banned words (line 107):** Good, concise.
- **Style rules (lines 58-64):** Concise and necessary.

#### B.6 Edge cases & error conditions
- **Empty `npc_roster`:** `_npc_roster.j2` handles with `{% if npc_roster -%}` — correct
- **Empty `inventory`:** `_inventory.j2` renders "Nothing of note." — correct
- **Empty `conditions`:** `_conditions.j2` handles with `{% if conditions -%}` — correct
- **Empty `location`:** `_location.j2` falls back to "Unknown" — correct
- **Empty `recent_turns`:** `_recent_turns.j2` handles with `{% if recent_turns %}` — correct
- **Empty `prior_history`:** Line 44 handles with `{% if prior_history and prior_history | length > 0 -%}` — correct
- **Empty `pending_beat`:** Lines 77-79 handle with `{% if pending_beat and pending_beat.type -%}` — correct
- **Empty `pacing_context`:** Lines 80-83 handle with `{% if pacing_context and pacing_context.outcome_hint -%}` — correct
- **Empty `rules_outcome`:** Lines 55-67 handle with `{% if rules_outcome and rules_outcome.impossible %}` / `{% elif rules_outcome and rules_outcome.rolled %}` / `{% elif rules_outcome and not rules_outcome.rolled %}` — correct
- **Empty `user_input`:** Lines 73-75 just show empty between delimiters — no guidance for what narrator should do when player input is empty (turn 1, auto-play)
- **No guardrail against excessive prose:** System prompt says "Default terse" but no explicit cap or guidance on what "terse" means in practice (word count, sentence count)
- **No guardrail against model ignoring fail-band outcomes:** System prompt says "BINDING" (line 29) but no explicit consequence for violation

#### B.7 User prompt completeness
- **User prompt is 84 lines:** Reasonable for narration context.
- **Missing `turn_no` direct usage:** `turn_no` is in `NarratorBoundary` and passed to template, but `narrate_user.j2` doesn't use it directly — only used in includes. This is fine.
- **Missing `curtain_call` usage:** `curtain_call` is passed in `narrate.py:253` and `narrate.py:108` but never rendered in `narrate_user.j2`. System prompt references `curtain_call` (line 78: "When `curtain_call` is active..."). This is a gap — user prompt should render curtain_call for the system prompt to use.
- **Missing `arc_hint_text` usage:** `arc_hint_text` is passed in `narrate.py:107` but never rendered. System prompt doesn't reference it either — dead variable.
- **Missing `arc_pressure_score` usage:** `arc_pressure_score` is passed in `narrate.py:106` but never rendered. System prompt doesn't reference it — dead variable.
- **Missing `ages` usage:** `ages` is in `NarratorBoundary` and passed in `narrate.py:249` but never rendered. System prompt doesn't reference it — dead variable.
- **Missing `resolved_arcs` usage:** `resolved_arcs` is in `NarratorBoundary` and passed in `narrate.py:109` but never rendered. System prompt doesn't reference it — dead variable.
- **`state` dict provides `location`, `inventory`, `scene.world_state`:** Correct — includes access these.
- **`current_objective` fallback to `state.long_term_objective`:** Lines 32-38 handle both — correct.

#### B.8 Findings:
- [ ] **Dead fields in `NarratorBoundary`:** `ages`, `resolved_arcs` — never used in template. Remove. **VALIDATED: confirmed.**
- [ ] **Dead render variables:** `arc_hint_text`, `arc_pressure_score` passed in `narrate.py:106-107` but never used in template. Remove. **VALIDATED: confirmed.**
- [ ] **`curtain_call` not rendered in user prompt:** System prompt references `curtain_call` (line 78) but user prompt never renders it. Add to `narrate_user.j2`. **INVALIDATED: `curtain_call` IS rendered at `narrate_user.j2:48-55`. Not dead.**
- [ ] **Tense ambiguity:** Line 1 says "Default past tense" but genre tone can override. Unclear if genre tone overrides past tense or if past tense applies to second person. Clarify. **VALIDATED: confirmed.**
- [ ] **Inventory constraint stated 3 times:** Lines 9, 17, 19. All within the same Inventory section — more about internal consolidation than cross-section redundancy. **PARTIALLY VALIDATED: confirmed, but all in one section so less impactful than originally noted.**
- [ ] **"Every sentence must advance" / "Each beat must advance":** Lines 58 and 72. Consolidate. **VALIDATED: confirmed.**
- [ ] **Empty `user_input` no guidance:** Lines 73-75 show empty delimiters. What should narrator do when player input is empty? **VALIDATED: confirmed.**
- [ ] **No explicit prose length cap:** "Default terse" is vague. Consider adding a word range (e.g., "50-150 words" or "2-5 sentences"). **VALIDATED: confirmed.**
- [ ] **NPC naming vs new character intro tension:** Line 54 says use exact proper names but line 39 says describe new characters' appearance. Clarify that new characters get a name on first introduction. **VALIDATED: confirmed.**
- [ ] **"Player input is truth" vs "pragmatic interpretation" conflict:** Lines 5 and 68 could conflict if model interprets "unclear" too broadly. Clarify priority. **VALIDATED: confirmed.**

### C. Extract Scene (step2a-scene)
**Files:** `extract_scene_system.j2`, `extract_scene_user.j2`, `context.py:SceneExtractBoundary`
**Arch doc:** `docs/architecture/step2a-scene.md`
**Includes:** `_npc_roster.j2`

#### C.1 Architecture alignment
- System prompt correctly implements NPC presence extraction, compendium updates, field requirements by tier, passive NPC extraction, party assignment, dedup rules, presence levels, bio examples
- User prompt provides narration, npc_roster, pc_name, turn_no — matches architecture doc inputs
- `npc_roster` comes from `build_npc_roster(comp)` — outputs dicts with id/name/title/bio/presence/mfl/position/last_presence_turn/last_seen_location/departed_reason
- Architecture doc mentions `tie` but prompt uses `bond` — rename not applied yet
- Architecture doc says "4 fields minimum" for named NPCs but prompt says "5 fields minimum" — discrepancy

#### C.2 Variable completeness & rendering
- `SceneExtractBoundary` declares: `narration`, `npc_roster`, `pc_name`, `turn_no`
- **Missing from `SceneExtractBoundary`:** `show_all_fields` — passed in `scene.py:33`, used in `_npc_roster.j2:8` to control whether motivation/fear/leverage/personality render for all NPCs vs just present ones
- **Type mismatch in `NPCRosterEntryBlock`:** `build_npc_roster()` returns dicts with `bond`, `departed_reason`, `personality_label`, `personality_traits`, `personality_speech_hint` — but `NPCRosterEntryBlock` only declares `id`, `name`, `title`, `bio`, `presence`, `motivation`, `fear`, `leverage`, `notes`, `last_presence_turn`, `last_seen_location`. Missing 5 fields.
- `_npc_roster.j2` uses `n.position` (line 6) but `build_npc_roster()` does NOT return `position` — dead field in template, always renders empty
- `_npc_roster.j2` uses `n.bond` (line 7) — returned by `build_npc_roster()` but not in `NPCRosterEntryBlock`
- `_npc_roster.j2` uses `n.departed_reason` (line 5) — returned by `build_npc_roster()` but not in `NPCRosterEntryBlock`
- `_npc_roster.j2` does NOT use `n.personality_traits`, `n.personality_label`, `n.personality_speech_hint` — `personality_registry` was removed from `build_npc_roster()` in I-24
- `show_all_fields` passed as `True` in `scene.py:33`, used in `_npc_roster.j2:8`. Since always `True`, the `{% else %}` branch is dead code.
- `turn_no` passed in `scene.py:31`, used in `_npc_roster.j2:9` for "X turns ago" display — correct
- `pc_name` passed in `scene.py:32`, used in `extract_scene_user.j2:1` — correct
- `narration` passed in `scene.py:29`, used in `extract_scene_user.j2:9` — correct
- `npc_roster` passed in `scene.py:30`, used in `extract_scene_user.j2:4-6` — correct

#### C.3 Schema/output discipline
- **Schema example uses `bond`** (line 21) — should be `tie` per rename
- **Field rules use `bond`** (line 36) — should be `tie`
- **Bio field says "TWO SENTENCES"** (line 32) but bio example for named NPCs (line 95) is actually THREE sentences. Contradiction.
- **Bio example for unnamed NPCs** (line 101) says "Missing appearance entirely" as incorrect, but field rules for unnamed NPCs say `bio` is mandatory. The example is correct to reject — just poorly worded.
- **Field requirements discrepancy:** Architecture doc says "4 fields minimum" for named NPCs (bio + personality + 2 of motivation/fear/leverage/tie). Prompt says "5 fields minimum" (bio + personality + motivation + 2 of fear/leverage/bond). Motivation is mandatory in prompt but not in doc's count.
- **`personality` field says "archetype_id"** — lists valid IDs. Good constraint.
- **`presence` says "REQUIRED for every NPC update — never omit it"** — good explicit constraint.

#### C.4 Internal consistency
- **`bond` → `tie`:** Line 36 says `bond`, architecture doc says `tie`. Rename not applied.
- **Line 69 field requirements:** "Named NPCs... Must have `bio` + `personality` + `motivation` + 2 of {fear, leverage, bond} = 5 fields minimum" — architecture doc says 4 fields minimum. Prompt's 5-field count includes motivation as mandatory, making it 5 total. Architecture doc is outdated.
- **Bio example (line 95) is 2 sentences:** "Tall with a jagged burn scar... Served five years..." — consistent with "TWO SENTENCES" rule on line 32. No contradiction.
- **Presence levels defined 3 times:** Lines 9-13 (extraction mandate), lines 76-89 (presence levels section), lines 43-51 (how to use compendium_npc_update). Overlapping content.
- **Dedup rules overlap:** Lines 115-122 (dedup pre-check) and lines 62-64 (NPC ID rules) cover the same ground.
- **"mandatory"/"MUST" used 7 times:** Lines 45, 48, 50, 51, 65, 69, 115. Could consolidate to reduce emphasis fatigue.

#### C.5 Duplication & verbosity
- **Presence levels defined 3 times:** Lines 9-13, lines 76-89, lines 43-51. Consolidate to one authoritative section.
- **Dedup rules overlap:** Lines 62-64 (NPC ID rules) and lines 115-122 (dedup pre-check) repeat the same "use existing ID" guidance.
- **Re-promotion guidance repeated:** Lines 49-51 and lines 119-120 both cover re-promotion from `known` to `present`.
- **"Default to extraction" stated once:** Line 15. Not 3 times as previously noted.
- **"mandatory"/"MUST" used 7 times:** Lines 45, 48, 50, 51, 65, 69, 115. Could consolidate to reduce emphasis fatigue.
- **System prompt ~133 lines:** Presence levels section (76-89) overlaps with earlier mentions. Could save ~15 lines.

#### C.6 Edge cases & error conditions
- **Empty `npc_roster`:** `_npc_roster.j2` handles with `{% if npc_roster -%}` — correct
- **Empty `narration`:** No explicit guard. If narration is empty string, LLM might still emit NPC updates from stale context. Should be handled by engine (skip extraction if no narration).
- **Empty `pc_name`:** Falls back to "Unnamed" in template — correct
- **NPC with no bio:** Field rules say bio is mandatory for every NPC. No template guard needed since this is a system constraint.
- **No guard against empty `compendium_npc_update` array:** System prompt says "omit fields entirely when there is no change" (line 131) but doesn't explicitly say "omit the entire array if empty."
- **No guard against LLM emitting personality for unnamed NPCs:** Field rules say "Do NOT add personality" for unnamed NPCs, and engine blocks it via guard in `npcs.py`. Good defense in depth.
- **`departed_reason` in schema example (line 21):** Shows `departed_reason` as a field but doesn't indicate it's conditional on `presence: "departed"`. Field rules (line 40) say it's required when `presence` is `"departed"`. Schema example should clarify this.

#### C.7 User prompt completeness
- **Minimal user prompt:** Only 10 lines. Relies on system prompt for all extraction rules. Correct design.
- **Missing `show_all_fields`:** Passed in `scene.py:33` but not in `SceneExtractBoundary`. Affects `_npc_roster.j2` rendering.
- **Missing `turn_no` usage:** `turn_no` is in `SceneExtractBoundary` and passed to template, but `extract_scene_user.j2` doesn't use it directly. Only used in `_npc_roster.j2:9`. This is fine — the include uses it.
- **No `state` dict:** Scene extractor doesn't receive full state, only compendium-derived npc_roster. Correct — scene extraction doesn't need full state.

#### C.8 Findings:
- [ ] **`show_all_fields` missing from `SceneExtractBoundary`:** Passed in `scene.py:33`, used in `_npc_roster.j2:8`. Add to boundary model. **VALIDATED: confirmed.**
- [ ] **`NPCRosterEntryBlock` type mismatch:** Missing `tie`, `departed_reason`, `personality_label`, `personality_traits`, `personality_speech_hint` — all returned by `build_npc_roster()`. Add for type safety. **VALIDATED: confirmed.** Note: `bond` already renamed to `tie` in `build_npc_roster()` output.
- [ ] **`position` is a dead field in `_npc_roster.j2`:** `build_npc_roster()` does NOT return `position`, so `n.position` always renders empty. Either add `position` to `build_npc_roster()` output or remove from template. **VALIDATED: confirmed.**
- [ ] **`show_all_fields` always `True`:** `scene.py:33` passes `show_all_fields: True`, making the `{% else %}` branch in `_npc_roster.j2:8` dead code. Either make it configurable or remove the dead branch. **VALIDATED: confirmed.**
- [ ] **Schema uses `bond` not `tie`:** Lines 21 and 36. Rename to `tie`. **RESOLVED: `extract_scene_system.j2` already uses `tie` (lines 21, 36). Rename applied.**
- [ ] **Field requirements discrepancy:** Architecture doc says 4 fields minimum for named NPCs; prompt says 5. Align — prompt's 5-field count (including mandatory motivation) is correct. **VALIDATED: confirmed. Prompt's 5-field count is correct; arch doc is outdated.**
- [ ] **Presence levels defined 3 times:** Lines 9-13 (extraction mandate), 43-51 (how to use compendium_npc_update), 76-89 (dedicated section). All 3 define presence levels with overlapping content. Dedicated section is most comprehensive; others are abbreviated. **VALIDATED: confirmed. Worst offender — ~40 lines of overlap in a 132-line prompt.**
- [ ] **Dedup rules overlap:** Lines 62-64 (NPC ID rules — brief) and lines 115-122 (dedicated dedup section — detailed). Both say "use existing ID from compendium." **VALIDATED: confirmed. Moderate overlap — NPC ID rules section could reference the dedup section instead of repeating.**
- [ ] **"mandatory"/"MUST" used 7 times:** Lines 45, 48, 50, 51, 65, 69, 115. Could consolidate to reduce emphasis fatigue. **VALIDATED: confirmed.**
- [ ] **No guard against empty `compendium_npc_update` array:** System prompt says "omit fields" but doesn't say "omit entire array if no changes." Add explicit guidance. **VALIDATED: confirmed.**
- [ ] **`departed_reason` in schema example should be conditional:** Line 21 shows `departed_reason` without indicating it's only for `presence: "departed"`. **VALIDATED: confirmed.**

### D. Extract State (step2b-state)
**Files:** `extract_state_system.j2`, `extract_state_user.j2`, `context.py:StateExtractBoundary`
**Arch doc:** `docs/architecture/step2b-state.md`
**Includes:** `_conditions.j2`, `_inventory.j2`, `_location.j2`

#### D.1 Architecture alignment
- System prompt correctly implements inventory/condition/location extraction, reason fields, narration authority, spatial reasoning, ID rules, pack inventory, quantities, field rules, state-presence rule, location change detection
- User prompt provides pc_name, conditions, inventory, location, intent, narration, turn_no — matches architecture doc inputs
- `pack_inventory` rendered in system prompt (not user prompt) — correct, it's static reference data
- Architecture doc describes state extraction — correct

#### D.2 Variable completeness & rendering
- `StateExtractBoundary` declares: `conditions`, `inventory`, `location`, `intent`, `turn_no`, `narration`
- **Missing from `StateExtractBoundary`:** `pc_name` — used in `extract_state_user.j2:1`. `pack_inventory` passed to system prompt but not in boundary model.
- `show_age` set locally in `extract_state_user.j2:3` — correct, controls age display in `_conditions.j2`
- `_conditions.j2` uses `show_age` and `turn_no` — both available (`show_age` set locally, `turn_no` from context)
- `_inventory.j2` uses `inventory` — available from context
- `_location.j2` uses `location` — available from context

#### D.3 Schema/output discipline
- Schema example shows `inventory_change_reason` as a string — correct, field rules say it's a one-phrase string
- Schema example shows `inventory_update` with `id`, `name`, `notes` — correct, field rules say patches include name changes and notes updates
- Schema example shows `inventory_remove` with `id` — correct, field rules say set `amount` to count consumed
- Schema example shows `inventory_add` with `id`, `name`, `notes`, `amount`, `canonical_id` — correct, field rules say include `canonical_id`
- Schema example shows `pc_condition_remove` with `id` — correct
- Schema example shows `pc_condition_add` with `id`, `label`, `description`, `turns_remaining: 5` — correct, 5 is in 5-6 turns range for significant wounds
- Schema example shows `location_change` with `id`, `name`, `description` — correct
- Schema example shows `location_description` as a string — correct
- **Schema example doesn't show `inventory_change_reason: "none"` for no-change case:** Field rules say "If no change: 'none'." Example should clarify this default.
- **Schema example doesn't show empty arrays:** Field rules say "empty arrays are never valid." Good — example omits empty arrays.
- **`canonical_id` emphasized as CRITICAL:** Good, prevents ID mismatches.
- **Duration guidance for `turns_remaining`:** 1-2 turns (sensory), 3-4 turns (minor), 5-6 turns (significant), 7+ turns (major), "permanent" (won't heal without intervention). Clear and actionable.
- **Condition removal guidance:** Fresh (≤3 turns) needs explicit resolution; Moderate (4-7 turns) can remove if cause ended; Old (>7 turns) can remove if narration moved past. Clear.
- **Stat-to-condition heuristics:** Combat failure → wounded/bleeding; Failed wits → frightened/drugged; Failed str/dex → exhausted; Decisive success → short-lived positive (focused, determined, etc.); Ally aids → brief positive (guided, fortified, etc.). Clear.

#### D.4 Internal consistency
- **Narration authority stated 4 times:** Lines 1 ("ground changes in narration"), 3 ("narrator is authoritative on prose"), 14 ("## Narration is the sole authority"), 16 ("Ground all changes in what the narration confirms"). Could consolidate.
- **Spatial reasoning (lines 22-30) and ID rules (lines 32-42) are different concerns:** Spatial reasoning covers WHEN to update vs create. ID rules cover WHAT ID to use. No overlap.
- **State-presence rule stated once:** Lines 117-119. Location change detection (lines 121-124) is a different concern. No duplication.
- **`turns_remaining` duration guidance (lines 95-101) and condition removal guidance (lines 104-108) are different concerns:** Duration tells you what TTL to assign. Removal tells you when to remove. No overlap.
- **"When in doubt" stated 2 times:** Lines 102, 108. Acceptable — different contexts (assigning duration vs removing conditions).
- **`inventory_change_reason` field rules are consistent:** "REQUIRED if any inventory field is non-empty" + "If no change: 'none'" means: when changes exist, set to descriptive phrase; when no changes, set to "none". Not contradictory.
- **`condition_change_reason` emphasized as CRITICAL (line 12):** Good, prevents ValueError.
- **CRITICAL used 4 times:** Lines 12, 36, 75, 91. Acceptable — each addresses a different critical failure mode.

#### D.5 Duplication & verbosity
- **System prompt ~125 lines:** Some sections could be tighter.
- **Narration authority stated 4 times:** Lines 1, 3, 14, 16. Could consolidate to one authoritative statement.
- **CRITICAL used 4 times:** Lines 12, 36, 75, 91. Acceptable — each addresses a different critical failure mode.

#### D.6 Edge cases & error conditions
- **Empty `conditions`:** `_conditions.j2` handles with `{% if conditions -%}` — correct
- **Empty `inventory`:** `_inventory.j2` renders "Nothing of note." — correct
- **Empty `location`:** `_location.j2` falls back to "Unknown" and "No description." — correct
- **Empty `intent`:** Template handles with `{% if intent and intent.intent -%}` — correct
- **Empty `narration`:** No explicit guard. If narration is empty, LLM might still emit changes from stale context. Should be handled by engine.
- **Empty `pack_inventory`:** System prompt handles with `{% if pack_inventory %}` — correct
- **Condition cap (max 5 active):** Field rules say "Total active conditions must not exceed 5" — good constraint
- **Condition add cap (max 2 per turn):** Field rules say "Max 2 per turn" — good constraint
- **Positive condition cap (max 1 per turn):** Field rules say "Max 1 per turn" for decisive success and ally aids — good constraint
- **No guard against LLM emitting `inventory_add` and `inventory_remove` for same ID:** Field rules say "Never emit `inventory_add` and `inventory_remove` for the same ID in one turn" — good explicit prohibition

#### D.7 User prompt completeness
- **Minimal user prompt:** 16 lines. Relies on system prompt for extraction rules. Correct design.
- **Missing `pc_name` in `StateExtractBoundary`:** Used in `extract_state_user.j2:1`. Add to boundary model.
- **Missing `pack_inventory` in `StateExtractBoundary`:** Passed to system prompt. Add for type safety.
- **`show_age = true` set locally:** Controls age display in `_conditions.j2`. Correct.
- **`intent` optional:** Only rendered when present. Correct.
- **`location` always renders:** Falls back to "Unknown" if empty. Correct.

#### D.8 Findings:
- [x] **Missing from `StateExtractBoundary`:** `pc_name`, `pack_inventory` — both used in templates but not in boundary model. **LEFT AS-IS: low priority, engine passes via dict.**
- [x] **Narration authority stated 4 times** → **collapsed to single "Grounding" section**. **RESOLVED.**
- [x] **Schema example doesn't show `inventory_change_reason: "none"`:** Field rules say set to "none" when no changes. **LEFT AS-IS: field rules already state this clearly.**
- [x] **No guard against empty narration:** Should be handled by engine. **LEFT AS-IS: engine concern, not prompt fix.**

### E. Record (step2c-record)
**Files:** `record_system.j2`, `record_user.j2`, `context.py:StorytellerBoundary`
**Arch doc:** `docs/architecture/step2c-record.md`
**Includes:** `_arc.j2`, `_thread_list.j2`, `_recent_turns.j2`

#### E.1 Architecture alignment
- System prompt correctly implements thread operations, arc resolution, curtain call, outcome summary, actions
- User prompt provides narration, current_objective, all_threads, world_state, resolved_arcs, recent_turns, prior_history, turn_no, band, pc_name — matches architecture doc inputs
- Architecture doc describes backward-looking scribe step — correct
- `thread_creation_cooldown` mentioned in arch doc as engine gate, not rendered in prompt — correct (engine-enforced)

#### E.2 Variable completeness & rendering
- `StorytellerBoundary` declares: `narration`, `npc_roster`, `location`, `conditions`, `inventory`, `current_objective`, `all_threads`, `world_state`, `intent`, `pacing_context`, `recent_turns`, `prior_history`, `turn_no`, `band`, `scene_phase`, `curtain_call`, `allowed_beat_types`, `pending_beat`, `recent_beats`, `resolved_arcs`
- Engine passes: `narration`, `current_objective`, `all_threads`, `world_state`, `resolved_arcs`, `recent_turns`, `prior_history`, `turn_no`, `band`, `pc_name`
- **Missing from `StorytellerBoundary`:** `pc_name` — used in `record_user.j2:1`. Add to boundary model.
- **Dead fields in `StorytellerBoundary`:** `npc_roster`, `location`, `conditions`, `inventory`, `intent`, `pacing_context`, `scene_phase`, `curtain_call`, `allowed_beat_types`, `pending_beat`, `recent_beats` — none passed by record engine. Remove.
- `resolved_arcs` is NOT dead — passed in `record.py:67`, used in `_arc.j2:14-18` for "Recently Resolved Arcs" display. Correct.

#### E.3 Schema/output discipline
- Schema example shows `thread_update` with `reason` field (line 12) — not in field rules. Either add to field rules or remove from example.
- Schema example shows `thread_add` with `id`, `type`, `summary`, `urgency` — correct, field rules say `summary` is required.
- `major_update_signal` values ARE defined in schema example: `"advancement|setback"` (line 12). Clear.
- `thread_resolve.world_state_candidate` usage not explained in field rules. Add guidance.
- `thread_resolve.resolution_state` values ARE defined in schema example: `"resolved|failed|abandoned"` (line 11). Clear.
- `thread_update.progress` example is just `...` — no specific example to exceed the 5-7 word limit. Correct.
- `actions` example shows 4 choices — consistent with field rules.
- `arc_resolve` example shows `resolution` and `long_term_objective` — correct.
- `goal_update` example shows `long_term_objective` — correct.

#### E.4 Internal consistency
- **Urgency escalation (3+ turns unaddressed → escalate) vs engine auto-dormant (8 turns):** Different thresholds. Prompt's 3-turn escalation would trigger much earlier than engine's 8-turn dormancy. **UPDATED (2026-07-07):** These rules should be removed from Record entirely. The Record is a log-keeper, not a decision-maker. Thread lifecycle rules (urgency escalation, scene phase thread guidance, curtain call forcing) belong in the Narrator prompt. The Record should only log what the Narrator did.
- **`thread_creation_cooldown` in arch doc vs no cooldown in prompt:** Handled by engine, not prompt. Document this separation.
- **Curtain call guidance for CLIMAX phase:** **UPDATED (2026-07-07):** Should be removed from Record prompt. The Narrator writes the prose and decides when threads are resolved. The Record should only log the Narrator's decisions, not force them.
- **No curtain call guidance for other phases:** Correct (not applicable).
- **Outcome summary: "one sentence" — clear.**
- **Actions: "exactly 4 choices" — clear.**
- **Actions grounding rules: "at least one NPC by name" and "at least one inventory item or location feature" — clear.**
- **Arc resolution vs goal_update are different concerns:** Arc resolution ends the arc (lines 59-67). Goal update changes the arc's direction (line 69). No overlap.

#### E.5 Duplication & verbosity
- **System prompt ~94 lines:** Reasonable for complexity.
- **Thread rules are extensive but necessary:** Thread lifecycle is complex.
- **"CRITICAL" used 9 times:** Lines 39, 41, 43, 45, 47, 49, 63, 65, 69. Could reduce to top 3-4 most important. Dilutes emphasis.
- **Thread ID rules stated 6 times:** Lines 25, 41, 43, 45, 47, 49. Consolidate.

#### E.6 Edge cases & error conditions
- **Empty `all_threads`:** Template handles with `{% if all_threads %}` — correct
- **Empty `world_state`:** Template handles with `{% if world_state %}` — correct
- **Empty `prior_history`:** Template handles with `{% if prior_history %}` — correct
- **Empty `recent_turns`:** `_recent_turns.j2` handles with `{% if recent_turns %}` — correct
- **Empty `band`:** Template handles with `{% if band %}` — correct
- **Missing `current_objective`:** `_arc.j2` handles with `{% if current_objective and current_objective.long_term_objective %}` — correct
- **Missing `narration`:** No explicit guard. If narration is empty, LLM might still emit thread operations from stale context. Should be handled by engine.

#### E.7 User prompt completeness
- **User prompt is 34 lines:** Reasonable for record extraction.
- **Missing `pc_name` in `StorytellerBoundary`:** Used in `record_user.j2:1`. Add to boundary model.
- **`resolved_arcs` IS used:** Passed in `record.py:67`, used in `_arc.j2:14-18`. Not dead.
- **`band` controls rules_outcome section rendering:** Correct.
- **`all_threads` set to `threads` before `_thread_list.j2` include:** Correct.
- **`world_state` renders conditionally:** Correct.
- **`prior_history` renders conditionally:** Correct.
- **`_recent_turns.j2` include unconditional:** Correct.
- **Narration section unconditional:** Correct.

#### E.8 Findings:
- [x] **Missing from `StorytellerBoundary`:** `pc_name` — used in `record_user.j2:1`. **RESOLVED: added to boundary model.**
- [x] **Dead fields in `StorytellerBoundary`:** ~~`npc_roster`~~, ~~`location`~~, ~~`conditions`~~, ~~`inventory`~~, ~~`intent`~~, ~~`pacing_context`~~, ~~`scene_phase`~~, ~~`curtain_call`~~, ~~`allowed_beat_types`~~, ~~`pending_beat`~~, ~~`recent_beats`~~ — none passed by record engine. **RESOLVED: removed dead fields, added `pc_name`.**
- [x] **Schema example `thread_update` has `reason` field:** Not in field rules. **RESOLVED: `reason` is in field rules (line 12 of schema, used for thread_update).**
- [x] **`thread_resolve.world_state_candidate` not explained:** Field rules don't explain when to use it. **LEFT AS-IS: low priority, can be added later.**
- [x] **Urgency escalation vs auto-dormant threshold:** Prompt says 3+ turns, engine auto-dormant at 8. **UPDATED (2026-07-07): These rules should be removed from Record entirely. The Record is a log-keeper, not a decision-maker. Thread lifecycle rules belong in the Narrator prompt.**
- [x] **`thread_creation_cooldown` not in prompt:** Arch doc mentions cooldown gate, prompt doesn't render it. Handled by engine. **RESOLVED: documented as engine-gated.**
- [x] **"CRITICAL" used 9 times** → **4 times now** (progress new fact, don't resolve non-existent threads, never update+resolve same thread, don't emit empty arc_resolve). **RESOLVED.**
- [x] **Thread ID rules stated 5 times** → **consolidated to 1 section**. **RESOLVED.**
- [x] **No guard against empty narration:** Should be handled by engine. **LEFT AS-IS: engine concern, not prompt fix.**
- [x] **Record prompt thread lifecycle rules should be removed:** Curtain call forcing, scene phase thread rules, "3+ turns → resolve" rule, urgency escalation rules, thread sustainability rules. These belong in the Narrator prompt. The Record should only log what the Narrator did. **RESOLVED (2026-07-07): All rules stripped from Record prompt. Thread authority added to Narrator prompt. Curtain call soft guidance moved to Narrator user prompt.**

### F. World (step2d-world)
**Files:** `world_system.j2`, `world_user.j2`
**Arch doc:** `docs/architecture/step2d-world.md`

#### F.1 Architecture alignment
- System prompt correctly implements beat generation, schema, generation rules, diversity, roll band guidance
- User prompt provides npc_roster, arc, pacing_context, recent_beats, allowed_beat_types, rules_outcome, narration — matches architecture doc inputs
- Architecture doc describes async beat-candidate generation step — correct
- **No `WorldBoundary` model in `context.py`:** World prompts are the only ones without a typed boundary model. All other 6 pairs have boundary models.

#### F.2 Variable completeness & rendering
- Engine passes: `npc_roster`, `arc`, `pacing_context`, `recent_beats`, `allowed_beat_types`, `rules_outcome`, `narration`
- `npc_roster` filtered to `presence in ["present", "nearby"]` in `world.py:47` — correct
- `rules_outcome` constructed as `{"band": ..., "rolled": ...}` from `state.meta.last_rules_outcome` — correct
- `allowed_beat_types` derived from `scene_phase` and `pc.directive` via `derive_allowed_beat_types()` — correct
- `arc` passed as full arc dict — template uses `arc.threads` — correct
- `pacing_context` passed as-is — template checks `pacing_context.directive or pacing_context.outcome_hint` — correct
- `recent_beats` passed as list — template iterates with `b.turn`, `b.type`, `b.effect` — correct

#### F.3 Schema/output discipline
- Schema example shows `[{"type": "...", "effect": "...", "npcs": ["npc_id_1", "npc_id_2"]}]` — correct structure
- `type` values listed: `complication|revelation|opportunity|breathing_room|pressure|twist|setback|escalation|callback` — matches GMBeat model
- `effect` described as "Short concrete sentence" — clear
- `npcs` described as "List of NPC IDs" — clear, but schema example uses placeholder IDs (`npc_id_1`) instead of real IDs
- **Schema example `npcs` uses placeholder values:** Should use a realistic example like `["silas_reed"]` to match field rules' example
- **`npcs` field rules say "You MUST populate this field with actual NPC IDs":** Good explicit constraint
- **`npcs` field rules say "never emit an empty array unless purely environmental":** Good explicit constraint
- **No explicit constraint on `effect` length:** Field rules say "Short concrete sentence" but no word limit. Acceptable for creative generation.
- **No explicit constraint on `npcs` count:** Field rules don't say how many NPCs per beat. Acceptable — depends on beat complexity.

#### F.4 Internal consistency
- **Generation priority order (lines 15-19):** Cross-NPC blending → NPC/Thread/Arc blending → Single-NPC depth → Environmental. Clear hierarchy.
- **Diversity rules (lines 29-38):** Look at last 2 `recent_beats`, avoid repeating types. Hard constraint for escalation. Build on recent beats, don't repeat. Clear.
- **Roll band guidance (lines 41-45):** crit_success/success → reward; partial → tension; setback/fail → recovery; no roll → neutral. Clear.
- **Phase alignment (line 23):** `type` MUST be from `allowed_beat_types`. Engine enforces this via phase validation. Correct.
- **Action rule (line 20):** "Every beat must show an NPC or the world taking action." Clear constraint.
- **Quantity (line 26):** "Emit 2-3 candidates. Zero is acceptable if no good beat fits." Clear.
- **NPC preference (line 25):** "Prefer NPC-driven beats" — consistent with priority order.
- **Hard constraint for escalation (line 33):** "This is not a suggestion — it is a rule." Good emphasis.

#### F.5 Duplication & verbosity
- **System prompt ~46 lines:** Lightweight, appropriate for beat generation.
- **"Build, don't repeat" stated 3 times:** Lines 34, 35, 36. Could consolidate.
- **Diversity section ~13 lines:** Could be tighter. The "Explicitly build on recent beats" examples (lines 35-38) are helpful but could be integrated into the "Build, don't repeat" rule.
- **Hard constraint for escalation (line 33):** Good emphasis, but the rule is very specific. Could be a separate "Escalation rule" section for clarity.

#### F.6 Edge cases & error conditions
- **Empty `npc_roster`:** `world_user.j2` handles with `{% if npc_roster %}` — correct. Engine also filters to present/nearby before passing.
- **Empty `arc.threads`:** `world_user.j2` handles with `{% if arc and arc.threads %}` — correct
- **Empty `pacing_context`:** `world_user.j2` handles with `{% if pacing_context and (pacing_context.directive or pacing_context.outcome_hint) %}` — correct
- **Empty `recent_beats`:** `world_user.j2` handles with `{% if recent_beats %}` — correct
- **Empty `allowed_beat_types`:** `world_user.j2` handles with `{% if allowed_beat_types %}` — correct
- **Empty `rules_outcome`:** `world_user.j2` handles with `{% if rules_outcome and rules_outcome.rolled %}` — correct
- **Missing `narration`:** No explicit guard. If narration is empty, LLM might still generate beats from stale context. Should be handled by engine.
- **No NPCs present:** Template says "No present or nearby NPCs. Generate beats from narration + threads alone." — correct fallback.

#### F.7 User prompt completeness
- **User prompt is 46 lines:** Reasonable for world generation.
- **No `pc_name`:** Not used in world template. Correct — world generation doesn't need PC name.
- **`npc_roster` renders bio, motivation, fear, leverage, bond, personality:** Good — provides full NPC profiles for beat generation. **Note:** `bond` should be `tie` per rename.
- **`arc.threads` renders type, urgency, id, summary:** Good — provides thread context.
- **`pacing_context` renders directive and outcome_hint:** Good — provides pacing guidance.
- **`recent_beats` renders turn, type, effect:** Good — provides beat history for diversity.
- **`allowed_beat_types` renders as comma-separated list:** Good — provides phase constraints.
- **`rules_outcome` renders band (only if rolled):** Good — provides roll context.
- **`narration` renders full text:** Good — provides narrative context.

#### F.8 Findings:
- [ ] **No `WorldBoundary` model:** World prompts are the only ones without a typed boundary model. Consider adding one for consistency. **LEFT AS-IS: low priority.**
- [x] **Schema example `npcs` uses placeholder values:** `["npc_id_1", "npc_id_2"]` should use realistic IDs. **LEFT AS-IS: placeholder values are intentional for schema examples.**
- [x] **`bond` → `tie` rename:** `world_system.j2` line 23 prose example still said "bond she shares". `pack.py:43` CompendiumEntry used `bond` field. **RESOLVED: both fixed.**
- [x] **No guard against empty narration:** Should be handled by engine. **LEFT AS-IS: engine concern.**

### G. Seed (prepare + narrate)
**Files:** `prepare_seed_system.j2`, `prepare_seed_user.j2`, `narrate_seed_system.j2`, `context.py` (seed-related blocks)
**Arch doc:** `docs/architecture/step2c-record.md` (seed section) + `docs/architecture/OVERVIEW.md` (seed pipeline)

#### G.1 Architecture alignment
- `prepare_seed_system.j2` correctly implements seed state generation, schema, hard constraints, generation order, NPC field requirements, personality archetypes, PC field rules, arc origin, session name, world state rules, key locations, PC situation, inventory rules, thread rules
- `prepare_seed_user.j2` correctly implements scenario context, player overrides, name pool, pool selection, JSON output discipline
- `narrate_seed_system.j2` correctly implements opening narrative instructions, actions, outcome summary
- `narrate_seed_user.j2` doesn't exist — user text is just "Generate the opening_narrative, actions, and outcome_summary now."
- **No `SeedBoundary` model in `context.py`:** Seed prompts are handled separately from the main turn pipeline. Consistent with architecture.
- Architecture doc for seed is in `step2c-record.md` (seed section) + `OVERVIEW.md` (seed pipeline)

#### G.2 Variable completeness & rendering
- `_build_prepare_seed_messages` passes: `scenario`, `overrides`, `name_pool`, `name_seed`, `pool_selection`
- `_build_narrate_seed_messages` passes: `pc.name`, `pc.tagline`, `pc.situation`, `location.id`, `location.name`, `location.description`, `arc_origin`, `pool_selection`, `setting_info`, `compendium_npcs`, `arc`
- `prepare_seed_system.j2` uses `scenario`, `pool_selection`, `scenario.constraints`, `scenario.pc_situation_schema`, `scenario.factions` — all available
- `prepare_seed_user.j2` uses `scenario`, `overrides`, `name_pool`, `name_seed`, `pool_selection` — all available
- `narrate_seed_system.j2` uses `setting_info`, `pc`, `location`, `arc_origin`, `arc`, `compendium_npcs`, `pool_selection` — all available

#### G.3 Schema/output discipline
- **Schema uses TypeScript syntax (`{ seed_state: { ... } }`):** Fixed — replaced with full JSON example with realistic values.
- `pc.situation` schema is dynamic: `{% if scenario and scenario.pc_situation_schema %}{% for s in scenario.pc_situation_schema %}{{ s.key }}: string{% endfor %}{% else %}key: string{% endif %}` — correct, adapts to pack
- `compendium.npcs` schema: `{snake_case: {name, title, bio, presence, bond?, motivation?, fear?, leverage?, personality?}}` — correct nested structure
- **`arc.completed_threads: null`:** Set to `null` in seed state. Correct — no completed threads at game start.
- `scene.world_state` schema: `Array<{id, text, tier, permanent, valence, expires_turn}>` — correct
- `world.locations` schema: `Array<{id, name, description, status, tags}>` — correct
- **Thread type values listed:** `threat`, `opportunity`, `complication`, `revelation` — clear
- **Thread count hard limits:** 1-2 non-dormant, up to 3 dormant, total 4-5 — clear
- **Thread quality:** "medium-term tension capable of sustaining 5-10 turns" — clear guidance
- **Inventory rules:** 3-6 items, specific names, firearms paired with ammo, no exotic weapons — clear
- **PC field rules:** name (given + family), tagline (5-10 words), bio (2-4 sentences), stats (4 integers) — clear
- **Session name:** 3-6 words, evocative, captures tone and setting — clear
- **World state rules:** 1 sentence each, max 4 entries, must include neutral/boon valence — clear
- **Key locations:** 4-5 named places, ordered accessible to unknown, 1-2 breadcrumbs — clear
- **PC situation:** structured facts, values may include names, omit if no relevant fact — clear

#### G.4 Internal consistency
- **NPC field requirements stated 4 times:** Lines 11 (mandatory present), lines 84-97 (presence + field counts), line 120 (pc_situation NPCs), line 91 (named NPC 5-field minimum). Redundant.
- **`bond` → `tie`:** Line 36 schema uses `bond?`, line 69 user prompt uses `npc_bond.description`, line 86 system prompt uses `bond`. Rename not applied.
- **Hard constraints section (lines 46-53):** Dynamically generated from `scenario.constraints`. Correct.
- **Generation order (lines 56-76):** Wide to narrow — world facts → locations → arc origin → PC situation → campaign arc → opening scene → inventory. Logical flow.
- **Cross-field consistency (lines 73-76):** `world_state` consistent with `arc_category`, PC bio reflects `character_dynamic`. Good.
- **NPC role alignment (lines 78-80):** Roles consistent with cultural/historical context. Good.
- **Thread IDs:** "2-4 word broad conceptual buckets. No proper nouns." Clear.
- **Thread summaries:** "one sentence (8-15 words), describing a SITUATION, not an objective." Clear.
- **Thread quality examples:** Good summary vs bad summary — clear.
- **PC situation names:** "When mentioning family members, always include a full name" — clear.
- **Inventory item names:** "start with a capital letter" — clear.
- **Opening narrative:** "~700 words. Second person, present tense. Three movements" — clear structure.
- **Actions:** "Exactly 4 choices, 7-10 words each, active voice" — clear.
- **Outcome summary:** "One sentence (~10-20 words) summarizing the opening situation" — clear.

#### G.5 Duplication & verbosity
- **`prepare_seed_system.j2` ~191 lines:** Quite long. NPC field requirements repeated 4 times.
- **NPC field requirements stated 4 times:** Lines 11, 84-97, 120, 91. Consolidate into one authoritative section.
- **`prepare_seed_user.j2` ~90 lines:** Reasonable. JSON output discipline (lines 83-86) overlaps with output discipline (lines 88-90).
- **JSON output discipline vs output discipline:** Lines 83-86 say "Wrap in json code block" and "no hyphens as word separators." Lines 88-90 say "omit fields when no change." Different concerns — acceptable separation.
- **`narrate_seed_system.j2` ~105 lines:** Reasonable. Opening narrative instructions (lines 28-55) are detailed but necessary.
- **Actions requirements overlap:** Lines 93-99 have 7 requirements that could be tighter. "At least 2 must advance arc" and "At least 2 should reveal character" overlap slightly.

#### G.6 Edge cases & error conditions
- **Empty `scenario`:** `prepare_seed_system.j2` handles with `{% if scenario and scenario.constraints %}` — correct
- **Empty `overrides`:** `prepare_seed_user.j2` handles with `{% if overrides %}` — correct
- **Empty `name_pool`:** `prepare_seed_user.j2` handles with `{% if name_pool %}` — correct
- **Empty `pool_selection`:** Both templates handle with `{% if pool_selection %}` — correct
- **Empty `setting_info`:** `narrate_seed_system.j2` handles with `{% else %}` fallback to "HISTORICAL REALISM" — correct
- **Empty `compendium_npcs`:** `narrate_seed_system.j2` handles with `{% if compendium_npcs %}` — correct
- **Empty `arc`:** `narrate_seed_system.j2` handles with `{% if arc %}` — correct
- **Empty `pool_selection.scene_bundle`:** `narrate_seed_system.j2` handles with `{% if pool_selection and pool_selection.get("scene_bundle") %}` — correct
- **No present NPCs:** Engine enforces "at least 1 NPC with presence='present'" via soft validation in `prepare_seed()` (line 438). Good defense in depth.

#### G.7 User prompt completeness
- **`prepare_seed_user.j2` is 90 lines:** Reasonable for seed configuration.
- **Scenario context:** world_facts, narrator_rules, world_rules, factions, inspiration — all conditionally rendered.
- **Player overrides:** pc_hints, npc_hints, location_hints, arc_hints, free_form — all conditionally rendered.
- **Name pool:** pc, npc, location candidates + name_seed — correct.
- **Pool selection:** situation, arc, character_dynamic, moral_pressure, npc_bond, scene_bundle — correct.
- **JSON output discipline:** Wrap in json block, no hyphens, output only seed_state — correct.
- **`narrate_seed_user.j2` doesn't exist:** User text is hardcoded "Generate the opening_narrative, actions, and outcome_summary now." — minimal but sufficient.

#### G.8 Findings:
- [ ] **No `SeedBoundary` model:** Seed prompts don't have boundary models. Consistent with architecture (seed pipeline is separate), but consider adding for consistency.
- [ ] **Schema uses TypeScript syntax:** `{ seed_state: { ... } }` should use JSON syntax for clarity.
- [ ] **`bond` → `tie` rename in `prepare_seed_system.j2`:** Lines 38 (`bond?: string`), 86 (`bond` in NPC field list), 90 (`bond` in unnamed NPC rules), 91 (`bond` in named NPC field requirements). Rename to `tie`. Note: `npc_bond` in `prepare_seed_user.j2:68-69` is a different concept (pack's npc_bonds pool selection) — keep as-is.
- [ ] **NPC field requirements stated 4 times:** Lines 11, 84-97, 120, 91. Consolidate into one authoritative section.
- [ ] **`prepare_seed_system.j2` ~191 lines:** Quite long. NPC field requirements could be consolidated to save ~30 lines.
- [ ] **JSON output discipline vs output discipline overlap:** Lines 83-86 and lines 88-90 in `prepare_seed_user.j2`. Different concerns but close together.
- [ ] **Actions requirements overlap:** Lines 93-99 in `narrate_seed_system.j2`. "At least 2 must advance arc" and "At least 2 should reveal character" overlap slightly.
- [ ] **~700-word target fragile:** Hardcoded word count in `narrate_seed_system.j2:30`. LLMs are poor at counting words. Consider "medium-length opening" or range instead.

---

## Eval dumps for rendering

Primary dump: `evals/runs/2026-06-28_0.30.0-53-ge6b746b4_e6b746b/2038_allied-ww2_aggressive_25t/events.jsonl` (31 lines, multi-turn active gameplay)

Secondary dump for variety: `evals/runs/2026-06-28_0.30.0-53-ge6b746b4_e6b746b/` — check for space-western or golden-piracy saves for different scenario context.

Stream names: `ruling`, `narrate`, `scene`, `state`, `record`, `world`, `storytell`, `seed`

---

## Cross-cutting checks (applied after all pairs)

- Do all prompts use consistent terminology for the same concepts?
- Do boundary models in `context.py` match what templates actually consume?
- Are there dead variables in boundary models (defined but never used)?
- Are there variables used in templates but not defined in boundary models?
- Do section templates work correctly when included from different parent prompts?
- Are there contradictions between different prompts about the same game state?

### Cross-cutting finding 1: `NarratorBoundary` missing `turn_no`
- `turn_no` used in `_npc_roster.j2:9` and `_thread_list.j2:9,17`
- `NarratorBoundary` (context.py:234-259) does NOT declare `turn_no`
- Engine passes `turn_no` in `user_ctx` (narrate.py:98)
- Templates render at runtime (Jinja doesn't enforce types) but boundary contract is broken

### Cross-cutting finding 2: `NPCRosterEntryBlock` missing 5 fields
- `build_npc_roster()` returns `bond`, `departed_reason`, `personality_label`, `personality_traits`, `personality_speech_hint`
- `NPCRosterEntryBlock` (context.py:201-218) only declares `id`, `name`, `title`, `bio`, `presence`, `motivation`, `fear`, `leverage`, `notes`, `last_presence_turn`, `last_seen_location`
- `_npc_roster.j2` uses all 5 fields

### Cross-cutting finding 3: `curtain_call` never rendered in user templates
- Referenced in `narrate_system.j2:78` and `record_system.j2:73,75` (system prompts)
- Passed by engines (narrate.py:108, StorytellerBoundary:313)
- Never rendered in any user template
- Narrator/storyteller knows about curtain_call from system prompt but never sees its actual value

### Cross-cutting finding 4: `pc_name` missing from 2 boundary models
- `StateExtractBoundary` (context.py:274-286): missing `pc_name`, but `extract_state_user.j2:1` uses `{{ pc_name }}`. Engine passes it (state.py:38).
- `StorytellerBoundary` (context.py:289-317): missing `pc_name`, but `record_user.j2:1` uses `{{ pc_name or "Unnamed" }}`. Engine passes it (record.py:72).

### Cross-cutting finding 5: `thread_update.reason` accepted by model but ignored by engine
- `ThreadUpdate` model has `reason: str | None = None` (state.py:204)
- `record_system.j2:12` schema example includes `reason`
- `turn_state.py:46-110` never reads `reason` when applying updates
- Accepted by Pydantic but ignored by engine — dead field

### Cross-cutting finding 6: `thread_resolve.world_state_candidate` undocumented in prompt
- `ThreadResolution` model has `world_state_candidate: str | None = None` (state.py:194)
- `record_system.j2:11` schema example includes it
- Engine stores it in `state["world_state_candidates"]` for thread sanitizer (turn_state.py:296-302)
- `record_system.j2` never explains what `world_state_candidate` does or when to use it

### Cross-cutting finding 7: `thread_creation_cooldown` not in prompt
- Config has `thread_creation_cooldown: int = 3` (config.py:183)
- Engine enforces it (turn_state.py:559-563)
- `record_system.j2` never mentions it
- Note: E.5 already notes this — consolidate

### Cross-cutting finding 8: `thread_add` schema example incomplete
- `record_system.j2:13` shows `thread_add` as `{"id": "...", "type": "threat", "summary": "...", "urgency": "normal"}`
- `ArcThread` model has `major_updates`, `resolution_state`, `outcome`, `resolved_turn`, `last_updated_turn`, `added_turn`, `urgency_set_turn`
- Engine validates against `ArcThread` (turn_state.py:559-626)
- Schema example omits 6 model fields

### Cross-cutting finding 9: `urgent_threads.progress` format mismatch
- `ruling.py:52` passes raw `major_updates` dicts with `kind`/`text`
- `ruling_user.j2:20-22` expects `{{ p.kind }}` and `{{ p.text }}`
- `record.py:40` formats progress via `_fmt_progress()` into strings like `"[ADVANCEMENT] Telegram received"`
- `_thread_list.j2:11` renders `{{ entry }}`
- Same underlying data formatted differently in ruling vs record prompts

### Cross-cutting finding 10: `arc_pressure_score` dead
- Passed in `user_ctx` (narrate.py:106), declared in `NarratorBoundary:259`
- Referenced in `_arc.j2:3` comment but never actually rendered
- `arc_hint_text` IS rendered (`_arc.j2:9-11`)

### Cross-cutting finding 11: `thread_resolve` CRITICAL count
- `record_system.j2:35,45,47,63` — 4 times as "CRITICAL"
- Combined with `thread_add` rules (lines 43, 49) and `thread_update` rules (line 41), thread ID rules stated 6 times total
- Note: E.5 says "5 times" — corrected to 6
- **VALIDATED:** 9× "CRITICAL" in rendered output (lines 39, 41, 43, 45, 47, 49, 63, 65, 69). Top 3-4 most important would suffice.

### Cross-cutting finding 12: `bond` → `tie` rename not applied
- `extract_scene_system.j2`: lines 21, 36 — **RESOLVED**, already uses `tie`
- `world_system.j2`: lines 16, 18, 21, 22 — **RESOLVED** in tags (`tie`), but line 23 prose example still says "bond she shares"
- `world_user.j2`: line 9 — **RESOLVED**, uses `n.tie`
- `prepare_seed_system.j2`: lines 38, 86, 90, 91 — **RESOLVED**, uses `tie`
- `sections/_npc_roster.j2`: line 7 — **RESOLVED**, uses `n.tie`
- `ruling_user.j2`: line 12 — **RESOLVED**, uses `n.tie`
- `npc_roster.py`: lines 45, 100 — **RESOLVED**, uses `tie`
- `pack.py:43` — **REMAINING**, `bond` as data key name (schema layer)
- `world_system.j2:23` — **REMAINING**, prose example says "bond she shares" instead of "tie she shares"

### Cross-cutting finding 13: Dead fields in `StorytellerBoundary`
- `npc_roster`, `location`, `conditions`, `inventory`, `intent`, `pacing_context`, `scene_phase`, `curtain_call`, `allowed_beat_types`, `pending_beat`, `recent_beats` — 11 fields not passed by record engine
- **Note:** Engine passes these via the `state` dict to the template, so they're not truly dead in the rendered prompt. The boundary model is just wrong about what it declares.

### Cross-cutting finding 14: Missing from boundary models
- `SceneExtractBoundary`: `show_all_fields`
- `StateExtractBoundary`: `pc_name`, `pack_inventory`
- `StorytellerBoundary`: `pc_name`
- `NarratorBoundary`: `turn_no`

### Cross-cutting finding 15: Dead template fields
- `_npc_roster.j2:6` — `n.position` always renders empty (not returned by `build_npc_roster()`)
- `_npc_roster.j2:8` — `{% else %}` branch dead when `show_all_fields=True`

### Summary after cross-cutting review

| Category | Count |
|----------|-------|
| Boundary model ↔ engine mismatches | 5 (#1, #2, #3, #4, #13) |
| Dead template variables | 2 (#3, #10) |
| Schema ↔ model mismatches | 4 (#5, #6, #7, #8) |
| Terminology consistency | 1 (#11) |
| Design inconsistencies | 2 (#9, #12) |
| Missing from boundary models | 1 (#14) |
| Dead template fields | 1 (#15) |
| **Total cross-cutting findings** | **16** |

### Combined totals

| Category | Count |
|----------|-------|
| Individual pair findings (A-G) | 58 |
| Cross-cutting findings | 16 |
| **Grand total** | **74** |

### Redundancy summary (validated 2026-07-03)

All redundancy claims validated against rendered output from `1434_space-western_25t`, turn 8.

**Confirmed redundancies (high confidence):**
1. **Scene Extract — presence levels defined 3×** (~40 lines overlap in 132-line prompt, ~30% of prompt)
2. **Scene Extract — dedup rules overlap** (~15 lines, NPC ID rules section repeats dedup section)
3. **Record — "CRITICAL" used 9×** (counted in rendered output, dilutes emphasis)
4. **Record — thread ID rules stated 5-6×** (~15 lines, lines 41-49 particularly overlapping)
5. **Narrate — "Every sentence must advance" / "Each beat must advance"** (Style vs Pacing sections)
6. **State Extract — narration authority stated 4×** (all in opening section, ~4 lines)

**Partially confirmed (less impactful than noted):**
7. **Narrate — inventory constraint stated 3×** (all within same Inventory section, internal consolidation only)

**Worst offenders:**
- **Scene Extract** — ~55 lines of redundant presence/dedup guidance. Could save ~15-20 lines by consolidating.
- **Record** — ~20 lines of emphasis inflation (9× "CRITICAL" + 5× thread ID rules). Could save ~10 lines by reducing emphasis and consolidating.
