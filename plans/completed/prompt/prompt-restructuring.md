# Prompt restructuring + ARC UPDATE removal

## Status
`completed`

## Phases

4 phases: (1) remove ARC UPDATE dead code from turn.py and prompt, (2) restructure narrate_system.j2, (3) restructure narrate_user.j2, (4) restructure storytell_system.j2 and storytell_user.j2.

## Issue

The narrator and storyteller system prompts are poorly structured for LLM attention (especially Gemma 4). Hard rules are scattered — inventory constraint is buried in Style, player-input-is-truth starts at line 26, the NO REPETITION rule is at line 130. NPC guidance is split across 3 sections. The user prompt buries Player Input near the bottom but not at the very bottom.

Separately, the `## ARC UPDATE` section in narrate_system.j2 (lines 70-87) instructs the narrator to emit structured JSON after its prose. In practice, the narrator **never** emits ARC UPDATE blocks — the instruction is completely ignored. The extraction code at turn.py:1491-1519 never fires. The `## ARC UPDATE` section is 18 lines of dead prompt content wasting tokens and confusing the LLM. The extraction code (`_extract_narrator_arc_update`, `_ARC_UPDATE_RE`, lines 1713-1734) is dead code.

Storyteller system prompt has similar structural issues: the long output schema and GM beat guidance occupy the mid-section, with behavioral rules mixed throughout.

## Solution

Remove the ARC UPDATE prompt section and extraction code (dead weight, never fires). Restructure both system prompts using the hierarchy: (1) task/role, (2) hard rules, (3) behavioral guidance, (4) formatting/output. Merge NPC sections into one. Move inventory hard constraint out of Style into hard rules. Consolidate the anti-repetition directive (plan narrator-prompt-anti-repetition.md handles content changes — this plan handles ordering and consolidation only). Reorder user prompt sections so the most important signal comes last (recency bias). Update "Prior Turns (Compacted)" header to "Prior History". Apply analogous restructuring to storyteller prompts.

## Firm decisions

1. System prompt hierarchy: task/role → hard rules → behavioral guidance → formatting/output.
2. Hard rules section includes: Player Input Is Truth, Inventory Hard Constraint, Never Repeat Prior Narration (from anti-repetition plan, content TBD there), Fail-band outcomes are BINDING.
3. Behavioral guidance includes: NPCs (merged into one section), Campaign Arc context (prose guidance only), Pacing, Pragmatic Interpretation.
4. **ARC UPDATE section removed entirely** from narrate_system.j2 — the narrator never emits it, it wastes 18 lines of system prompt, and the extraction code is dead.
5. **`_extract_narrator_arc_update()`, `_ARC_UPDATE_RE`, and the extraction call block at turn.py:1491-1519 are removed.** `_ALLOWED_NARRATOR_ARC_KEYS` dict is also removed.
6. `_merge_arc_update()` in delta_builder.py stays — still used by storyteller pipeline for thread operations.
7. NPC sections merge: NPCs in Scene + Mortal Stakes + NPC Naming → one `## NPCs` section.
8. "Inventory is a hard constraint" moves out of Style into the hard rules section.
9. "Style" section keeps only stylistic guidance (spatial clarity, avoid tropes, direct dialogue, tight prose, colorful imagery).
10. User prompt: Player Input, Result/Band, Beat/Pacing directives at the bottom (recency bias). Context at the top.
11. "Prior Turns (Compacted)" → "Prior History".
12. Storyteller prompts get analogous restructuring.
13. Anti-repetition content changes are in the separate plan (narrator-prompt-anti-repetition.md). This plan only restructures ordering and section boundaries — any new anti-repetition directive from that plan should land in the hard rules section.

## Non-goals

- Changing prompt content/wording beyond what restructuring requires (that's the anti-repetition plan's job).
- Changing the NPC roster template, `_arc.j2`, or any section includes.
- Changing `CampaignArc` model fields (`visible_goal`, `thematic_question`, `discovered_truths`, etc.) — they stay for seed-time initialization and the `_arc.j2` include.
- Changing `narrate.py` Python code — only `.j2` templates and turn.py dead code removal.
- Adding or removing narrative rules — only reorganizing what exists.

## Risks, Ambiguities, and Blockers

- **Anti-repetition gap during execution:** Phase 2 removes three scattered anti-repetition clauses (line 12 clause, line 40 clause, lines 130-132 block) and replaces them with a `## Never repeat prior narration` placeholder. Until the anti-repetition plan is executed, the system prompt has zero anti-repetition rules — the LLM may repeat narration during this gap. Execute the anti-repetition plan immediately after this plan to minimize the gap.
- **Prompt regression:** Restructuring changes token positions, which can alter LLM behavior. Validate by running turns and observing output.
- **Storyteller restructuring scope:** The storyteller system prompt is 143 lines with dense formatting specs. Moving the output schema requires care (LLMs expect format instructions early).
- **ARC UPDATE removal is safe:** The narrator never emits this block. The extraction code path is never triggered. No eval, tv, or template code references it. `_merge_arc_update` remains for the storyteller path.

## Implementation — Phase 1: Remove ARC UPDATE dead code

### Context files to load

- `ccya/engine/turn.py` (lines 1491-1519, lines 1713-1734)
- `ccya/prompts/narrate_system.j2` (lines 70-87)

### Detailed steps

#### Step 1.1 — Remove ARC UPDATE section from narrate_system.j2

**File:** `ccya/prompts/narrate_system.j2`

**What:** Delete the entire `## ARC UPDATE (optional, after narration)` section (lines 70-87). This includes the `<<<ARC_UPDATE_START>>>` / `<<<ARC_UPDATE_END>>>` example, the rules list, and the "IMPORTANT: Hidden truths are for internal reasoning only" subsection.

**Why:** The narrator never emits ARC UPDATE blocks. Verified against current saves and both eval runs — zero turns produce ARC UPDATE output. The instruction wastes 18 lines of system prompt tokens and confuses the LLM by asking it to produce structured JSON.

**Validation:** `make check` passes. The file renders correctly (no broken Jinja2).

#### Step 1.2 — Remove ARC UPDATE extraction code from turn.py

**File:** `ccya/engine/turn.py`

**What:** Remove three blocks:
1. Lines 1491-1519: The entire "Extract narrator arc_update block if present" block, including `_ALLOWED_NARRATOR_ARC_KEYS`, the `CampaignArc.model_validate()` call, `_merge_arc_update` call, the merge/copy logic, and the exception handler.
2. Lines 1713-1716: The `_ARC_UPDATE_RE` compiled regex.
3. Lines 1719-1734: The `_extract_narrator_arc_update()` function.

Keep `_merge_arc_update` import at line 65 — still used by storyteller pipeline (lines 1355, 1366, 1455, 1480).

**Why:** Dead code. The narrator never emits ARC UPDATE blocks, so this extraction logic never fires.

**Validation:** `make check` passes. `grep -rn "ARC_UPDATE_START\|_extract_narrator_arc_update\|_ARC_UPDATE_RE\|_ALLOWED_NARRATOR_ARC_KEYS" ccya/` returns no hits. `_merge_arc_update` (legitimate storyteller pipeline function) and `delta.arc_update` (field on StateDelta model) should still exist — they are not being removed.

#### Step 1.3 — Update docs/repomap.md

**File:** `docs/repomap.md`

**What:** Remove the line at ~123 that reads: `- ARC_UPDATE JSON example includes "thematic_question" field alongside existing discovered_truths and visible_goal — matches _ALLOWED_NARRATOR_ARC_KEYS which already accepts this key (turn.py lines 1416-1419)`. Update narrator system prompt description to note that ARC UPDATE has been removed.

**Why:** The repomap currently references ARC UPDATE features that no longer exist.

**Validation:** `make check` passes.

### Tests to write or update

No tests to write or update (tests are temporarily removed during refactor).

### REPOMAP updates required

- Remove ARC_UPDATE and `_ALLOWED_NARRATOR_ARC_KEYS` references from narrate_system.j2 and turn.py entries
- Note that narrator no longer emits structured output

## Implementation — Phase 2: Restructure narrate_system.j2

### Context files to load

- `ccya/prompts/narrate_system.j2` (full file — after Phase 1 removals, ~114 lines)

### Detailed steps

#### Step 2.1 — Restructure narrate_system.j2 into 4 sections

**File:** `ccya/prompts/narrate_system.j2`

**What:** Rewrite the file with the following section order. All content is moved, not created. After Phase 1, the ARC UPDATE section is already gone. Line numbers reference the original file (132 lines) for source identification.

**Section 1 — Task/role**:
- Original line 1 (task description, second person, 2-4 paragraphs, output prose only)

**Section 2 — Hard rules** (never violate):
- `## Player input is truth` (original lines 26-40) — full section including conflict example and fallback
- `## Inventory` — merge original `## Items and inventory` bullets (lines 20-22) with `## Inventory is a hard constraint` (line 24) into one inventory section
- `## Fail-band outcomes are BINDING` (original lines 111-125)
- `## Never repeat prior narration` — placeholder for anti-repetition plan. Single line: `{# Anti-repetition directive: see narrator-prompt-anti-repetition.md #}`

**Section 3 — Behavioral guidance**:
- `## NPCs` — merge original `## NPCs in scene` (lines 45-52), `## Mortal stakes + agency` (lines 54-56), and `## NPC naming` (lines 58-63) into one section. Order: BEHAVIOR DRIVERS paragraph → NPC RE-USE bullet → NPC QUANTITY RULE bullet → mortal stakes/death content → naming rules → non-present NPC reference paragraph. Remove redundant section headers.
- `## Style` (original lines 10-18) — without inventory content (moved to hard rules) and without anti-repetition clauses (moved to hard rules placeholder). Keep only: spatial clarity, avoid tropes, direct dialogue, NPC/location interaction, visceral/gory/sexual details, brief new character descriptions, tight prose, colorful imagery.
- `## Pragmatic interpretation` (original lines 42-43)
- `## Pacing` — merge original pacing paragraph (line 8) and `## Scene outcome` (lines 107-109: hold/advance/transition directive). Remove "Do not spend more than one sentence bridging from the previous turn" from line 40 (anti-repetition plan owns this).
- `## Campaign arc context` (original lines 65-68 — the prose guidance only, not the JSON format which was removed in Phase 1)

**Section 4 — Formatting/output**:
- `## Output discipline` (original lines 127-128)
- `## Markdown` (original lines 89-93)

**Dynamic sections at the very end** (unchanged):
- `{% if world_rules %}## Universe rules...{% endif %}`
- `{% if narrator_rules %}## Genre tone...{% endif %}`

**What moves where (mapping):**

| Original section | New position |
|---|---|
| Opening paragraph (line 1) | Section 1 — Task/role |
| Pacing paragraph (line 8) | Section 3 — `## Pacing` |
| Bullets (lines 5-6) — NPC consequences, character mentions | Section 3 — `## NPCs` (opening) |
| `## Style` (lines 10-18) | Section 3 — `## Style` (minus inventory, minus anti-repetition) |
| `## Items and inventory` (lines 20-22) | Section 2 — merged into `## Inventory` |
| `## Inventory is a hard constraint` (line 24) | Section 2 — merged into `## Inventory` |
| `## Player input is truth` (lines 26-40) | Section 2 — `## Player input is truth` |
| `## Pragmatic interpretation` (lines 42-43) | Section 3 — `## Pragmatic interpretation` |
| `## NPCs in scene` (lines 45-52) | Section 3 — `## NPCs` (merged) |
| `## Mortal stakes + agency` (lines 54-56) | Section 3 — `## NPCs` (merged) |
| `## NPC naming` (lines 58-63) | Section 3 — `## NPCs` (merged) |
| `## Campaign Arc context` (lines 65-68) | Section 3 — `## Campaign arc context` |
| `## ARC UPDATE` (lines 70-87) | **Removed in Phase 1** |
| `## Markdown` (lines 89-93) | Section 4 — `## Markdown` |
| `{% if world_rules %}## Universe rules` (lines 94-98) | End — dynamic |
| `{% if narrator_rules %}## Genre tone` (lines 99-103) | End — dynamic |
| `## Scene outcome` (lines 107-109) | Section 3 — `## Pacing` (absorbed) |
| `## Fail-band outcomes` (lines 111-125) | Section 2 — `## Fail-band outcomes are BINDING` |
| `## Output discipline` (lines 127-128) | Section 4 — `## Output discipline` |
| `**NO REPETITION RULE:**` (lines 130-132) | Section 2 (placeholder, content removed) |

**Key constraints:**
- Do NOT add new rules or change wording of any existing rule. Only move and reorganize.
- The anti-repetition plan owns the content of `## Never repeat prior narration`. This step creates the section header with placeholder comment only.
- Scene outcome (lines 107-109: hold/advance/transition directive) merges into `## Pacing` since it's pacing guidance.
- The `**NO REPETITION RULE:**` content at lines 130-132 is removed (placeholder in hard rules replaces it). The anti-repetition plan will add the new directive.
- Line 12's clause "Don't repeat known facts or restate conditions already mentioned" is removed (will be replaced by anti-repetition plan's new directive).
- Line 40's clause "Do not spend more than one sentence bridging from the previous turn" is removed (will be replaced by anti-repetition plan's new directive).

**Why:** LLMs weight early and late positions more heavily. Hard rules near the top get strong adherence. Formatting/output at the bottom gets read-last attention. Behavioral guidance in the middle is processed but not over-weighted.

**Validation:** `make check` passes. The file renders correctly (no missing variables, no broken Jinja2).

## Implementation — Phase 3: Restructure narrate_user.j2

### Context files to load

- `ccya/prompts/narrate_user.j2` (full file — 99 lines)
- `ccya/prompts/sections/_npc_roster.j2`, `_arc.j2`, `_location.j2`, `_inventory.j2`, `_world_state.j2`

### Detailed steps

#### Step 3.1 — Reorder narrate_user.j2 sections by importance (most important last)

**File:** `ccya/prompts/narrate_user.j2`

**What:** Reorder sections so context is first and action signal is last, leveraging LLM recency bias. New order:

1. `## Player Character` (PC info — name, tagline, stats, conditions)
2. `## Inventory` (via include — hard constraint reference)
3. `## Location` (via include — scene setting)
4. `## Characters` (via NPC roster include — important context but not action signal)
5. `## World State` (via include — durable facts)
6. `<<<TRACE_IMMUTABLE_START>>>` block (factions, name pool)
7. `## Scene Context` → `### Current Threads`
8. `## Prior History` (renamed from "Prior Turns (Compacted)")
9. `### Recent Turns`
10. `## Campaign Arc` (via include)
11. `### Past Resolutions`
12. `## This Turn's Result` (rules outcome, band, IMPOSSIBLE/BINDING)
13. `=== PLAYER INPUT ===`
14. Beat + Pacing/Outcome directives

The key change: Result, Player Input, and Beat/Pacing directives move to the very bottom (after all context), so they're the last thing the LLM reads before generating.

**Why:** Recency bias means the LLM weights what it reads last most heavily. Player input and the current turn's outcome are the most important signals for narration generation.

**Validation:** `make check` passes. The file renders correctly for a sample context.

## Implementation — Phase 4: Restructure storytell_system.j2 and storytell_user.j2

### Context files to load

- `ccya/prompts/storytell_system.j2` (full file — 143 lines)
- `ccya/prompts/storytell_user.j2` (full file — 48 lines)

### Detailed steps

#### Step 4.1 — Restructure storytell_system.j2 into 4 sections

**File:** `ccya/prompts/storytell_system.j2`

**What:** Apply the same hierarchy as narrate_system.j2: task/role → hard rules → behavioral guidance → formatting/output.

Current structure (line numbers approximate):
1. Task description (line 1)
2. `## Output schema` (lines 2-16) — JSON spec
3. `## Thread operations` (lines 18-41) — behavioral rules for thread management
4. `## actions` guidance (line 44)
5. `## outcome_summary` guidance (line 46)
6. `## World state rules` (lines 48-60)
7. Thread visibility/latent threads paragraph (line 62)
8. `## PacingContext guidance` (lines 64-74)
9. `## GM Beat guidance` (lines 76-131) — very long
10. `## Rules-outcome guidance` (lines 133-136)
11. `## State-presence rule` (line 138)
12. `## Output discipline` (lines 140-143)

New structure:

**Section 1 — Task/role** (opening line):
- Line 1 ("Extract suggested player actions, outcome summary...")

**Section 2 — Hard rules**:
- `## Output schema` — the JSON format spec (stays near top, it's a hard constraint the LLM must follow precisely)
- `## Output discipline` (original lines 140-143)
- `## State-presence rule` (original line 138)

**Section 3 — Behavioral guidance**:
- `## Actions` (original line 44 — the 4-choice rule)
- `## Outcome summary` (original line 46)
- `## Thread operations` (original lines 18-41)
- `## Rules-outcome guidance` (original lines 133-136)
- `## World state rules` (original lines 48-60)
- Thread visibility/latent threads paragraph (original line 62)
- `## PacingContext guidance` (original lines 64-74)

**Section 4 — GM Beat guidance** (at the end, since it's the most detailed behavioral section and the LLM benefits from reading it last before generating):
- `## GM Beat guidance` (original lines 76-131)

**Why:** The same primacy/recency logic applies. The JSON schema is a hard constraint. Output discipline and state-presence are hard rules. GM Beat guidance is the most detailed section and benefits from recency positioning.

**Validation:** `make check` passes. The file renders correctly.

#### Step 4.2 — Reorder storytell_user.j2 sections by importance

**File:** `ccya/prompts/storytell_user.j2`

**What:** Reorder sections so context is first and action signal is last. Current order is: NPC roster → location → conditions → inventory → arc → threads → world state → pacing context → last turn's narration → player_intent → CURRENT TURN NARRATION.

New order:
1. `## Current inventory` (via loop)
2. `## PC conditions` (via loop)
3. `## Characters` (via NPC roster include)
4. `## location`
5. Arc + threads (via _arc.j2 include + thread list)
6. Past resolutions
7. `## world_state` (via trace block)
8. `## pacing_context`
9. `## last turn's context`
10. `## player_intent`
11. `## rules_outcome` + band
12. `## CURRENT TURN NARRATION`

The current turn's narration and player intent move to the bottom.

**Why:** The current turn's narration is the most important signal for the storyteller — it should be the last thing read before generating.

**Validation:** `make check` passes. The file renders correctly for a sample context.

### Tests to write or update

No tests to write or update (tests are temporarily removed during refactor).

### REPOMAP updates required

- `docs/repomap.md` — note narrator and storyteller prompt templates restructured into task → hard rules → behavioral guidance → formatting/output hierarchy; ARC UPDATE section and extraction code removed; narrator no longer emits structured output; no API changes.