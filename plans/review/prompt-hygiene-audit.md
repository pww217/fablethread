# Prompt Hygiene and Structural Audit

## Status
`open`

## Part of
standalone

## Dependencies
- none — all prompt-only changes; no engine API changes
- can run in parallel with narration directive plan (narration-pacing-fixes.md) but executor must coordinate: both plans touch `narrate_system.j2` and `narrate_user.j2`; merge changes from both before committing

## Objective
The five extractor prompts share a large block of NPC context verbatim, costing ~150 tokens per pipeline per turn across 5 pipelines (~750 tokens/turn wasted). Several user prompts contain standing rules that belong only in system prompts — the system/user boundary is violated. The narration user prompt contains Jinja conditionals that reference variables never passed at render time (the `scene_pressure` wire bug, addressed mechanically in narration-pacing-fixes.md, but the template structure itself also needs cleanup). The JSON schema sections and schema rules sections have significant duplication — schema defines syntax, rules define guidance, but both currently contain constraint prose. Intent-verb examples in the progress extractor are under-specified, producing drift. And several system prompts contain token-heavy re-explanation of things already in AGENTS.md or the pack rules, which the LLM doesn't need re-stated per call. This plan performs a systematic audit and cleanup of all five extractor system/user prompts plus the narration pair.

## Non-goals
- Does not change the content or meaning of any rule — only placement, structure, and redundancy.
- Does not add new mechanics, new Jinja variables, or new extraction fields.
- Does not touch compactor prompts (separate concern).
- Does not address few-shot examples (those are in other plans).
- Does not change `narrate.py` or any Python — prompt files only.

## Affected files
| File | Change type | Summary of change |
|---|---|---|
| `ccya/prompts/sections/_present_npcs.j2` | modify | Add a `caller` param; render short form (id+name+stance only) for extractors, full form for narrator |
| `ccya/prompts/narrate_system.j2` | modify | Move any per-turn rules into system; audit for bloat; add NO REPETITION and NPC QUANTITY rules (coordinate with narration-pacing-fixes.md) |
| `ccya/prompts/narrate_user.j2` | modify | Ensure only turn-variable data here; strip standing rules; clean up dead conditionals (coordinate with narration-pacing-fixes.md) |
| `ccya/prompts/extract_progress_system.j2` | modify | Separate schema (syntax) from rules (guidance); add intent_verb few-shot; strip redundant re-explanation |
| `ccya/prompts/extract_progress_user.j2` | modify | Verify no standing rules; ensure only current-turn context |
| `ccya/prompts/extract_scene_system.j2` | modify | Audit schema vs rules duplication; strip redundant prose |
| `ccya/prompts/extract_scene_user.j2` | modify | Verify no standing rules |
| `ccya/prompts/extract_state_system.j2` | modify | Audit schema vs rules duplication; add zero-stack few-shot (from state-and-inventory-reliability.md) |
| `ccya/prompts/extract_state_user.j2` | modify | Verify no standing rules |
| `ccya/prompts/extract_compendium_system.j2` | modify | Audit if present; strip redundant prose |
| `docs/REPOMAP/prompts.md` | update | Document structural changes to each prompt file |

## Firm decisions

1. **System prompt = permanent rules.** Anything that is true on every turn — output format, schema syntax, field constraints, tone rules, prohibited behaviors — belongs in the system prompt. If it does not change turn to turn, it is not user prompt content.
2. **User prompt = current-turn context only.** Player input, current state snapshot, rendered mechanics, rules outcome, recent events, present NPCs for this turn. No instructions. No rules. No schema.
3. **Schema section = syntax only.** The JSON schema block defines field names, types, required/optional, and enum values. It contains no prose guidance. Example: `"intent_verb": {"type": "string", "description": "lemmatized action verb"}` — not `"intent_verb must be a physical action, not a mental state"` (that goes in Rules).
4. **Rules section = guidance only.** No field definitions. No type annotations. No enum lists. Guidance like "intent_verb must be a single lemmatized verb describing the physical action, not a mental or emotional state" belongs here, not in schema.
5. **`_present_npcs.j2` short form** for all extractors: `id | name | stance` only — ~60% token reduction per extractor call. Full form (bio, description, relationship) only for narrator.
6. **No redundant system prompt headers** re-stating what the pipeline is — "You are the progress extractor. Your job is to..." followed by three paragraphs of re-explanation before the schema. This must be reduced to one sentence max.

## Implementation — Phase 1: NPC Block Token Reduction

### Context files to load
- `ccya/prompts/sections/_present_npcs.j2`
- `ccya/prompts/extract_progress_user.j2`
- `ccya/prompts/extract_scene_user.j2`
- `ccya/prompts/extract_state_user.j2`
- `ccya/prompts/narrate_user.j2`

### Overview
Add a `caller` variable to `_present_npcs.j2`. When `caller == "narrator"`, render full NPC entries. Otherwise, render compact entries (id, name, stance only). Update all five `{% include %}` call sites to pass the appropriate caller value.

### Detailed steps

#### Step 1.1 — Add short-form branch to _present_npcs.j2

**File:** `ccya/prompts/sections/_present_npcs.j2`

**What:** Wrap the existing full NPC render in `{% if caller == "narrator" %}`. Add an `{% else %}` block that renders:
```
- {{ npc.id }} | {{ npc.name }} | {{ npc.stance or "neutral" }}
```

**Why:** Extractors don't need NPC backstory, description, or relationship prose. They need the id for delta keys, the name for text matching, and the stance for extraction context.

**Validation:** Render `_present_npcs.j2` with `caller="extractor"` and 3 NPCs. Confirm each renders as a single line. Render with `caller="narrator"`. Confirm full form.

***

#### Step 1.2 — Update call sites

**File:** `ccya/prompts/extract_progress_user.j2`, `extract_scene_user.j2`, `extract_state_user.j2`

**What:** At each `{% include "_present_npcs.j2" %}` call site, pass `caller="extractor"`.

**File:** `ccya/prompts/narrate_user.j2`

**What:** Pass `caller="narrator"` at its include site.

**Validation:** Render each extractor user prompt. Confirm NPC block is compact. Render narrate user prompt. Confirm full NPC block.

***

## Implementation — Phase 2: System/User Boundary Audit

### Context files to load
- All six system prompts: `narrate_system.j2`, `extract_progress_system.j2`, `extract_scene_system.j2`, `extract_state_system.j2`, `extract_compendium_system.j2`, and whatever the fifth extractor is
- All corresponding user prompts

### Overview
For each system/user pair: move standing rules out of user into system; move turn-variable context out of system into user (if any); strip repeated role-statement preambles down to one line; ensure schema and rules sections are cleanly separated.

### Detailed steps

#### Step 2.1 — Audit and fix narrate_system.j2 / narrate_user.j2

**File:** `ccya/prompts/narrate_system.j2`

**What:**
- Confirm every rule in `narrate_user.j2` that does not vary by turn is moved here.
- Add NO REPETITION RULE (coordinate with narration-pacing-fixes.md for identical text).
- Add NPC QUANTITY RULE (coordinate with narration-pacing-fixes.md for identical text).
- Reduce role-statement preamble to: `You are the narrator for a text-based RPG. Produce immersive, concise narration for the player's action.`
- Strip any re-statement of pack lore, world background, or rules that are already in the system context.

**File:** `ccya/prompts/narrate_user.j2`
- Remove any standing rules (things true on every turn).
- Confirm only these sections remain: player input, rules outcome (if rolled), state snapshot sections (inventory, conditions, location, present NPCs, recent events), mechanic directives (momentum, scene pressure, breathe, overwhelm — these are per-turn because their values change). Coordinate with narration-pacing-fixes.md for the strengthened momentum/de-escalation directives.

**Validation:** Render `narrate_system.j2`. Confirm it contains NO per-turn variable interpolations (no `{{ turn }}`, no `{{ momentum }}`, etc.). Render `narrate_user.j2`. Confirm it contains no standing rules prose.

***

#### Step 2.2 — Separate schema from rules in extract_progress_system.j2

**File:** `ccya/prompts/extract_progress_system.j2`

**What:**
- Find the JSON schema block. Strip all prose guidance from field descriptions — descriptions should be type annotations only (`"type": "string"`, `"description": "lemmatized present-tense verb"`).
- Find or create a `## Rules` section below the schema. Move all guidance prose here.
- Add `intent_verb` few-shot examples:

```
## intent_verb Examples
Correct:  "attack", "search", "pick", "bribe", "flee", "examine", "open", "hide"
Incorrect: "try", "attempt", "decide", "want", "notice", "feel" — these are mental states or meta-verbs, not actions
When the player writes "I try to break the lock": intent_verb = "break"
When the player writes "I attempt to sneak past": intent_verb = "sneak"
```

**Why:** The `intent_verb` drift traces directly to under-specified guidance. The few-shot clarifies the "outermost physical action" rule concretely.

**Validation:** Render the system prompt. Confirm schema block has no prose constraint sentences. Confirm `## Rules` section exists. Confirm intent_verb examples present.

***

#### Step 2.3 — Audit extract_scene_system.j2 and extract_state_system.j2

**Files:** `ccya/prompts/extract_scene_system.j2`, `ccya/prompts/extract_state_system.j2`

**What:** Same schema/rules separation as Step 2.2. Additionally:
- In `extract_state_system.j2`: add the zero-stack overdraw few-shot from state-and-inventory-reliability.md if not already present.
- In `extract_scene_system.j2`: confirm `npc_add` guidance specifies that unnamed groups must use a count-prefixed id (`guards_x4`, not `guards`).

**Validation:** Render both system prompts. Schema block contains no prose. Rules section contains no type/field definitions.

***

#### Step 2.4 — Reduce preamble bloat across all system prompts

**Files:** All five extractor system prompts.

**What:** Find any preamble block longer than 2 sentences that re-states what the pipeline does. Reduce to one sentence. Examples of what to cut:
- "Your role is critical to maintaining game state. Without accurate extraction, the game cannot function correctly." → Delete entirely.
- "You will receive the narration output from the narrator pipeline and the current state snapshot. Your job is to identify changes..." → Reduce to `"Extract state changes from narration. Output only changed fields."`

**Why:** Preamble bloat increases prompt length without increasing compliance. Models attend to instructions near task-relevant content, not paragraph-length role statements.

**Validation:** Each system prompt preamble (before the schema section) is ≤ 3 sentences.

***

### Tests to write or update
- `tests/test_prompts.py`: `test_npc_block_compact_for_extractors` — render `_present_npcs.j2` with `caller="extractor"`, assert each NPC is one line matching `id | name | stance`.
- `tests/test_prompts.py`: `test_no_standing_rules_in_user_prompts` — render each user prompt with a minimal fixture, assert no strings like `"You must"`, `"Never"`, `"Always"` appear (heuristic; review false positives manually).
- `tests/test_prompts.py`: `test_intent_verb_examples_in_progress_system` — render `extract_progress_system.j2`, assert `intent_verb Examples` section present.

### REPOMAP updates required
- `docs/REPOMAP/prompts.md`: Update entries for all seven modified prompt files. Note short-form NPC block change and `caller` parameter. Note schema/rules separation. Note preamble reduction.

### Risks
1. **`caller` variable not in Jinja context** — if the include site doesn't set `caller`, the `{% if caller == "narrator" %}` check defaults to false and all callers get short form. Acceptable safe fallback but narrator would break. Mitigation: set `caller="extractor"` as the default in `_present_npcs.j2` with `{% set caller = caller | default("extractor") %}`.
2. **Schema/rules separation may break extractor if the model relied on schema prose** — unlikely but possible. Monitor first eval run after change for extraction quality regression.
3. **Both this plan and narration-pacing-fixes.md touch the same `narrate_system.j2` file** — executor must apply both plans' changes in one commit to avoid conflicts.

## Ambiguities requiring resolution before execution
1. What is the exact Jinja syntax for passing variables to `{% include %}` in the template engine used? Jinja2 uses `{% include "file.j2" %}` with context variables passed via `with context` or `{% set %}` before the include. Executor must confirm which pattern is used in the existing includes before adding the `caller` variable.
2. Is there a fifth extractor (`extract_compendium`) that also includes `_present_npcs.j2`? Executor must grep all `*.j2` files for `_present_npcs` to find all call sites.

## TODO.md update
Add under **P2 — Quality / Prompting**:
```
- [ ] [Prompt Hygiene and Structural Audit](plans/prompt-hygiene-audit.md)
```
