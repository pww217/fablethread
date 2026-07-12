# GM Beat Overhaul — Scene-Driven Beat Generation

## Purpose

Replace storytell-generated beats with scene-driven beat generation: scene identifies candidate NPCs and writes a vague psychological pressure effect; storytell maps it to specific NPCs/threads; narrator does the creative pivot.

## Problem Statement

The storyteller currently receives full NPC psychological fields (motivation/fear/leverage) duplicated from what scene already has, plus a slimmed-down roster — wasting tokens on context the storyteller doesn't need to make beat decisions. Scene is the authority on who matters narratively; storytell is the authority on how it connects to threads. The current design passes scene's `npc_context` (full psychological fields) to storytell, which then re-evaluates the same data — duplicating work and wasting tokens.

## Constraints

- No new pipeline steps. Beat generation stays inside the existing storytell stream.
- Single LLM call per turn. No async/background execution.
- Storytell context must not grow meaningfully. Scene emits candidates + vague effect; storytell receives these + thread context + names-only roster. Not additive.
- Direct swap. No backwards compatibility. Delete unused fields, routes, config keys, models.
- Tests are temporarily removed during refactor — do not write or reference tests.
- Run `make check` (lint + typecheck) as a final step when ALL work is complete.

## Non-goals

- Async / background beat generation
- Separate pipeline step for beat generation
- Per-NPC beat emission (one beat per turn, as now)
- Dice-outcome-gated beats
- Beat anchored to specific thread ID
- Changes to beat TTL or lifecycle mechanics (2-turn TTL stays)
- Location candidates (environmental beats are fallbacks only)
- Deriving beat types from `effect` text for pacing calculations
- NPC rolls (deferred to future phase)

## Solution

Scene emits `candidate_npc_ids` (1-3) + `effect` (vague psychological pressure, ~5-7 words). Storytell receives these via `_ExtractionContext` and maps them to specific NPCs/threads, writing the final terse effect with specific `npc_id` + `driver`. Storytell gets names-only `npc_roster` instead of full psychological fields. This eliminates token duplication and gives each stage its proper domain: scene owns relevance, storytell owns thread mapping, narrator owns creative pivot.

## Firm decisions

1. `surface_as` is removed entirely from `GMBeat` model and all references. **Already done** — `surface_as` is not in the current `GMBeat` model (line 177-211).
2. `effect` is terse (~5-7 words), not a full sentence. "Voss fears exposure" not "The guard captain recognizes the PC from a previous encounter and demands to know why they're back."
3. Scene writes the vague effect; storytell maps it to specific NPCs. Scene is the authority on who matters narratively; storytell is the authority on how it connects to threads.
4. `candidate_npc_ids` is a strong signal, not a hard constraint. Storytell can override based on threads.
5. `npc_roster` for storytell is slimmed to id, name, title only. No psychological fields, no bios, no personalities. **Current `slim=True` mode includes `bio` — needs to be removed.**
6. `SceneExtractResult` gains `candidate_npc_ids: list[str]` and `effect: str`. `npc_context` is removed. **Still needs to be done.**
7. `_ExtractionContext` gains `candidate_npc_ids: list[str]` and `scene_effect: str`. `npc_context` is removed. **Still needs to be done.**
8. Storytell prompt receives `candidate_npc_ids` + `scene_effect` from extraction_ctx instead of `npc_context`. **Still needs to be done.**
9. New template `_npc_names.j2` replaces `_npc_context.j2` for storytell. Renders names only. **Still needs to be done.**
10. `npc_context` function `build_npc_context()` in scene.py is removed. **Still needs to be done.**
11. `candidate_npc_ids` max_length is 3.
12. `effect` is required (empty string default). No max length validation.
13. `npc_id` + `driver` on beat: optional fields, required when NPC is the source. `driver` is one of `motivation | fear | leverage`. **Already done** — `GMBeat` model has `npc_id` and `driver` fields (line 209-210).
14. Null effect with non-null npc_id → retriable error in pipeline. **Already done** — pipeline has post-parse validation at `pipeline.py:191-220`.
15. Driver/npc_id mismatch → no coercion.
16. `gm_beat` field name stays on `StorytellerResult`. Not renamed. **Already done.**
17. Beat history snapshot in `turn_state.py` uses `effect` instead of `surface_as`. **Already done** — `turn_state.py:472-476` uses `effect`.
18. History event `gm_beat` dict in `turn.py` uses `effect` instead of `surface_as`. **Already done** — `turn.py:471-474` uses `effect`.
19. Narrator prompt shows `type` + `effect`. **Already done** — `narrate_user.j2:88` shows `type` + `effect`. `surface_as` is already gone. Design says changes beyond replacing `type`+`surface_as` with `effect` are a non-goal.
20. Narrator system prompt updated to reference `effect` instead of `type` + `surface_as`. **Already done** — `narrate_system.j2:11` references `effect`.
21. `beat_narrative_chain` checker already uses `effect` — no changes needed. **Already done.**
22. `gm_beat_lifecycle` and `beat_phase_validity` checkers work with `effect` field as-is — no changes needed. **Already done.**
23. `StorytellerResult._nullify_invalid_gm_beat` validator stays — nullifies if type is falsy. **Already done.**
24. `storytell_system.j2` needs rewriting for scene-driven beat generation. **Still needs to be done** — current system prompt has `effect`/`npc_id`/`driver` but not scene-driven beat generation instructions.
25. `storytell_user.j2` needs Scene Input + NPC Names sections. **Still needs to be done** — current user prompt includes `_npc_context.j2` at line 10, needs to be replaced.

## Risks, Ambiguities, and Blockers

- **Storytell overriding scene's candidates.** This is expected behavior, not a bug. Storytell's core domain is threads — it may pick a different NPC if a thread strongly points elsewhere. The design accounts for this.
- **Scene's vague effect not mapping to any candidate.** Scene says "someone fears exposure" but candidates don't have a fear field. Storytell can override based on threads. This is fine.
- **Scene not writing effects.** If scene forgets or can't decide, storytell needs to fall back to generating from scratch. The prompt instruction tells storytell to map scene's suggestion OR generate if scene provided nothing.
- **Effect too vague to be useful.** "Someone fears exposure" — storytell maps it to "Voss fears exposure" based on candidates. Narrator interprets freely. This is the design.

## Status
`open`

## Phases

5 phases covering: (1) model changes, (2) scene extraction changes, (3) extraction context + pipeline wiring, (4) storytell prompt changes, (5) narrator prompt + validation + cleanup.

---

## Implementation — Phase 1: Model Changes

### Context files to load
- `ccya/models/extraction.py` — GMBeat, SceneExtractResult, StorytellerResult models
- `ccya/engine/extraction/context.py` — _ExtractionContext

### Notes on what's already done
- `GMBeat` model already has `effect`, `npc_id`, `driver` fields (line 208-210). `surface_as` is already removed.
- `StorytellerResult` already has `gm_beat` field. `_nullify_invalid_gm_beat` validator is present.
- `turn_state.py:472-476` already uses `effect` in beat history snapshot.
- `turn.py:471-474` already uses `effect` in history event `gm_beat` dict.

### Detailed steps

#### Step 1.1 — Replace `npc_context` in `SceneExtractResult` with `candidate_npc_ids` + `effect`

**File:** `ccya/models/extraction.py:118-122`

**What:** Replace `npc_context: list[dict[str, Any]] = Field(default_factory=list)` with `candidate_npc_ids: list[str] = Field(default_factory=list, max_length=3)` and `effect: str = ""` on `SceneExtractResult`.

**Why:** Scene is the authority on who matters narratively. It emits candidate IDs and a vague psychological pressure effect. Storytell maps these to specific NPCs/threads.

**Validation:** `ruff check ccya/models/extraction.py` — no lint errors. `mypy ccya/models/extraction.py` — no type errors.

#### Step 1.2 — Replace `npc_context` in `_ExtractionContext` with `candidate_npc_ids` + `scene_effect`

**File:** `ccya/engine/extraction/context.py:28-29`

**What:** Replace `npc_context: list[dict[str, Any]] = field(default_factory=list)` with `candidate_npc_ids: list[str] = field(default_factory=list)` and `scene_effect: str = ""` on `_ExtractionContext`.

**Why:** Same as Step 1.1 — extraction context is the same-turn passer. It carries scene's output to storytell.

**Validation:** `ruff check ccya/engine/extraction/context.py` — no lint errors. `mypy ccya/engine/extraction/context.py` — no type errors.

### Tests to write or update

Tests are temporarily removed during refactor. Skip.

---

## Implementation — Phase 2: Scene Extraction Changes

### Context files to load
- `ccya/engine/extraction/scene.py` — `build_npc_context()` function, scene extraction pipeline
- `ccya/prompts/extract_scene_system.j2` — scene system prompt

### Detailed steps

#### Step 2.1 — Remove `build_npc_context()` function

**File:** `ccya/engine/extraction/scene.py:13-41`

**What:** Delete the `build_npc_context()` function entirely. It builds `npc_context` from compendium — no longer needed.

**Why:** Scene no longer extracts psychological fields for storytell. It writes `candidate_npc_ids` + `effect` directly via its LLM prompt.

**Validation:** `ruff check ccya/engine/extraction/scene.py` — no lint errors.

#### Step 2.2 — Update scene system prompt to emit `candidate_npc_ids` + `effect`

**File:** `ccya/prompts/extract_scene_system.j2`

**What:** Add instructions to scene's system prompt: "Based on narration + NPC fields, identify 1-3 NPCs who are likely to act or be affected next turn. Write a vague effect describing the psychological pressure (~5-7 words). Output `candidate_npc_ids` and `effect` fields."

**Why:** Scene needs to know it's responsible for beat candidate selection and vague effect writing.

**Validation:** Render the prompt with `ev.py prompt-eval dump` to verify it renders correctly.

### Tests to write or update

Tests are temporarily removed during refactor. Skip.

---

## Implementation — Phase 3: Extraction Context + Pipeline Wiring

### Context files to load
- `ccya/engine/extraction/context.py` — `_build_extraction_context()` function
- `ccya/engine/extraction/pipeline.py` — `build_npc_context` import, `npc_context` assignment, storytell message building

### Notes on what's already done
- Pipeline already has post-parse validation for null effect with npc_id at `pipeline.py:191-220`. No changes needed.

### Detailed steps

#### Step 3.1 — Update `_build_extraction_context()` to copy `candidate_npc_ids` + `scene_effect`

**File:** `ccya/engine/extraction/context.py:74`

**What:** Replace `npc_context=list(scene_result.npc_context or [])` with `candidate_npc_ids=list(scene_result.candidate_npc_ids or [])` and `scene_effect=scene_result.effect or ""` in the `_ExtractionContext` constructor call.

**Why:** Extraction context is the same-turn passer. It needs to carry scene's new output to storytell.

**Validation:** `ruff check ccya/engine/extraction/context.py` — no lint errors. `mypy ccya/engine/extraction/context.py` — no type errors.

#### Step 3.2 — Remove `build_npc_context` import and `npc_context` assignment from pipeline

**File:** `ccya/engine/extraction/pipeline.py:15` (import), `pipeline.py:164-165` (assignment)

**What:** Remove `build_npc_context` from the import on line 15. Remove lines 164-165 that call `build_npc_context()` and assign to `extraction_ctx.npc_context`.

**Why:** `build_npc_context()` is deleted. `npc_context` no longer exists on `_ExtractionContext`.

**Validation:** `ruff check ccya/engine/extraction/pipeline.py` — no lint errors. `mypy ccya/engine/extraction/pipeline.py` — no type errors.

#### Step 3.3 — Pass `candidate_npc_ids` + `scene_effect` to storytell messages

**File:** `ccya/engine/extraction/storytell.py:75`

**What:** Replace `"npc_context": extraction_ctx.npc_context` with `"candidate_npc_ids": extraction_ctx.candidate_npc_ids` and `"scene_effect": extraction_ctx.scene_effect` in the `_render()` call for `storytell_user.j2`.

**Why:** Storytell needs scene's candidates and effect, not the old `npc_context` format.

**Validation:** `ruff check ccya/engine/extraction/storytell.py` — no lint errors. `mypy ccya/engine/extraction/storytell.py` — no type errors.

### Tests to write or update

Tests are temporarily removed during refactor. Skip.

---

## Implementation — Phase 4: Storytell Prompt Changes

### Context files to load
- `ccya/engine/extraction/storytell.py` — `_storytell_messages()` function, `npc_context` pass-through, `npc_roster` building
- `ccya/prompts/storytell_system.j2` — GM Beat section
- `ccya/prompts/storytell_user.j2` — NPC Context section, pending beat display
- `ccya/prompts/sections/_npc_context.j2` — current NPC context template (to be replaced)
- `ccya/engine/npc_roster.py` — `build_npc_roster()` slim mode

### Notes on what's already done
- `storytell_system.j2:78-87` already has `effect`, `npc_id`, `driver` in beat schema.
- `storytell_user.j2:47` already shows `effect`. `storytell_user.j2:57` already shows `effect` in recent beats.
- `storytell.py:63` already passes `slim=True` to `build_npc_roster()`.

### Detailed steps

#### Step 4.1 — Slim `npc_roster` to names only for storytell (remove `bio`)

**File:** `ccya/engine/npc_roster.py:44-50`

**What:** Remove `bio` from the slim mode output. Change `seen[nid] = {"id": nid, "name": name, "title": ..., "bio": ...}` to `seen[nid] = {"id": nid, "name": name, "title": ...}`.

**Why:** Design says "names only" — no psychological fields, no bios, no personalities. Storytell only needs names to map scene's vague effect.

**Validation:** `ruff check ccya/engine/npc_roster.py` — no lint errors.

#### Step 4.2 — Rewrite storytell system prompt GM Beat section for scene-driven beats

**File:** `ccya/prompts/storytell_system.j2:76-95`

**What:** Update the GM Beat section with scene-driven beat generation instructions. Key changes:
- Change `effect` guidance from "short concrete sentence" to "terse signpost ~5-7 words"
- Tell storytell to map scene's suggestion to specific NPCs from candidates (or override based on threads)
- Add "Scene is the authority on who matters narratively; you are the authority on how it connects to story structure"
- Add instructions on how to use `candidate_npc_ids` and `scene_effect` (variable data is shown in user prompt)
- Add: storytell may optionally blend effects from multiple candidates, and attach the beat to threads

**Why:** Storytell's job is mapping, not generation. It receives scene's vague effect and maps it to specific NPCs/threads. Design explicitly says storytell "optionally blends effects, attaches to threads."

**Validation:** Render the prompt with `ev.py prompt-eval dump` to verify it renders correctly.

#### Step 4.3 — Rewrite storytell user prompt

**File:** `ccya/prompts/storytell_user.j2`

**What:** Replace `{% include "sections/_npc_context.j2" %}` (line 10) with Scene Input section showing `candidate_npc_ids` and `scene_effect`. Add NPC Names section showing names from `npc_roster`.

**Why:** Storytell needs to see scene's candidates and effect, plus NPC names for mapping. Variable data goes in user prompt; instructions on how to use them go in system prompt.

**Validation:** Render the prompt with `ev.py prompt-eval dump` to verify it renders correctly.

#### Step 4.4 — Create `_npc_names.j2` template

**File:** `ccya/prompts/sections/_npc_names.j2`

**What:** New template. Renders NPC names from `npc_roster` (id, name, title). Simple list format.

**Why:** Storytell needs NPC names to map scene's vague effect to specific NPCs.

**Validation:** Render the template with `ev.py prompt-eval dump` to verify it renders correctly.

### Tests to write or update

Tests are temporarily removed during refactor. Skip.

---

## Implementation — Phase 5: Narrator Prompt + Cleanup

### Context files to load
- `ccya/prompts/narrate_system.j2` — Beat priority ordering
- `ccya/prompts/narrate_user.j2` — Beat rendering
- `ccya/ev/checkers/gm_beat.py` — `gm_beat_lifecycle` checker
- `ccya/ev/checkers/beat_phase_validity.py` — `beat_phase_validity` checker

### Notes on what's already done
- `narrate_system.j2:11` already references `effect`. No changes needed.
- `turn.py:471-474` already uses `effect` in history event `gm_beat` dict. No changes needed.
- `turn_state.py:472-476` already uses `effect` in beat history snapshot. No changes needed.
- Pipeline already has post-parse validation for null effect with npc_id at `pipeline.py:191-220`. No changes needed.
- `gm_beat_lifecycle` and `beat_phase_validity` checkers work with `effect` field as-is. No changes needed.

### Detailed steps

#### Step 5.1 — No change needed to narrator user prompt

**File:** `ccya/prompts/narrate_user.j2:86-88`

**What:** No change. Current prompt `**Beat:** {{ pending_beat.type | replace('_', ' ') | upper }} — {{ pending_beat.effect }}. Use this as creative guidance for the scene. Do not recite beat metadata directly in narration.` already shows `type` + `effect`. `surface_as` is already removed from the model. Design says changes beyond replacing `type`+`surface_as` with `effect` are a non-goal.

**Why:** Narrator should see `type` + `effect`. `surface_as` is already gone. No change needed.

**Validation:** Verify current prompt is correct.

#### Step 5.2 — Remove `_npc_context.j2` template

**File:** `ccya/prompts/sections/_npc_context.j2`

**What:** Delete the file. It's replaced by `_npc_names.j2`.

**Why:** `_npc_context.j2` renders full psychological fields — no longer needed. Storytell gets names only.

**Validation:** Verify no other files reference `_npc_context.j2` via grep.

### Tests to write or update

Tests are temporarily removed during refactor. Skip.

---

## Documentation Updates Required

Any code change touching a module, config key, model field, prompt, or public API requires corresponding updates to documentation. Stale docs are bugs.

### `docs/architecture/step2a-scene.md`

- Update flowchart: Scene now outputs `candidate_npc_ids` + `effect` in addition to `compendium_npc_update`.
- Update "Key forward dependency" section: Scene's output now feeds storytell's beat mapping.

### `docs/architecture/step2c-storytell.md`

- Update flowchart: Storytell now receives `candidate_npc_ids` + `scene_effect` from `_ExtractionContext` instead of `npc_context`.
- Update "GM Beat" section: Describe scene-driven beat generation. Scene writes vague effect; storytell maps to specific NPCs/threads.
- Update "Beat History" section: Verify it references `effect` instead of `surface_as`.
- Update "NPC Context" references: Remove `npc_context` from input list, add `candidate_npc_ids` + `scene_effect`.

### `docs/architecture/step2b-state.md`

- No changes needed — state extraction is unaffected.

### `docs/architecture/OVERVIEW.md`

- Update pipeline quick reference table: Step 2a output includes `candidate_npc_ids` + `effect`. Step 2c input includes `candidate_npc_ids` + `scene_effect` instead of `npc_context`.
- Update `_ExtractionContext` description: Carries `candidate_npc_ids` + `scene_effect` instead of `npc_context`.

### `docs/architecture/cross-pipeline.md`

- Update flowchart if needed to reflect new data flow (scene → candidates/effect → storytell).

### `docs/architecture/prompt-variable-contracts.md`

- Update `npc_context` variable contract: removed from storytell.
- Add `candidate_npc_ids` + `scene_effect` variable contracts for storytell.
- Add `_npc_names.j2` template contract.

### `docs/repomap.md`

- Update `SceneExtractResult` model description: `candidate_npc_ids` + `effect` instead of `npc_context`.
- Update `_ExtractionContext` description: `candidate_npc_ids` + `scene_effect` instead of `npc_context`.
- Update `build_npc_context()` reference: removed from scene.py.

### `AGENTS.md`

- No changes needed — build commands and signposts are unchanged.
