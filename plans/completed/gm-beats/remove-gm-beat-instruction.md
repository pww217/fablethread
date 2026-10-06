# Remove gm_beat instruction field — simplify Storytell output + narrator flexibility

## Status
`completed`

## Phases

4 phases: Remove `instruction` from GMBeat model, update all prompt templates to work without it, simplify turn lifecycle save/restore logic that served removed beat_disposition, and update tests/scenarios.

## Issue

Storytell must generate long instruction strings (≥40 chars) for gm_beat — adding token cost and LLM workload. These pre-written narrative directives can conflict with player input or pacing context since they carry specific storypoints from the previous turn's extraction into narration as fixed content rather than flexible guidance. The beat lifecycle save/restore around narration served `beat_disposition` which was already removed, making that code vestigial. Additionally, Storytell receives carried-over pending beat context in its prompt for disposition decisions — a feature whose purpose no longer exists after beat_disposition removal.

## Solution

Remove `instruction` field entirely from GMBeat model and StorytellerResult validation. Beat becomes `{type, surface_as}` only — metadata for the narrator to infer content from context (arc state, pacing directive, scene pressures). Simplify turn lifecycle by removing save/restore of pending_gm_beat around narration since it served removed disposition logic. Remove beat_hint generation in _compute_pacing_context and its display in narrate_user.j2 as unreachable dead code after simplification. Storytell emits lightweight beat signals instead of narrative prose; narrator runs free using type semantics + surface_as presentation guidance + pacing directive + arc threads as creative inputs.

## Firm decisions

1. `instruction` field is fully removed from GMBeat — no optional fallback, no migration path
2. `_validate_instruction_quality` validator and `_GM_BEAT_FILLER_PREFIXES` constant are deleted entirely
3. StorytellerResult._nullify_invalid_gm_beat only checks for type presence (not instruction)
4. Beat lifecycle save/restore around narration (turn.py lines 1052-1060) is removed — pending_gm_beat cleared after narration, not restored before extraction
5. Storytell no longer receives pending_gm_beat in its prompt context (removed from storytell_user.j2 and extraction.py)
6. beat_hint field removed from PacingContext class and _compute_pacing_context() since it becomes unreachable dead code without save/restore
7. Beat Hint section in narrate_user.j2 was already removed in a prior change; no edit needed
8. Beat expiry mechanism (`beat_expires_turn`) remains unchanged — still stored with turn_no + 2

## Non-goals

- Do not change beat lifecycle mechanics beyond removing save/restore (expiry, replace/clear logic stays the same)
- Do not add new fields to GMBeat in this plan
- Do not modify floor relief injection via `beat_locked` (turn.py:1193-1200) — still injects breathing_room beat when momentum is at minimum
- Do not rewrite narration prompt system or pacing context architecture beyond removing dead code

## Risks, Ambiguities, and Blockers

- Storytell may need stronger prompt guidance to emit useful beats without instruction examples — storytell_system.j2 beat guidance section references `instruction` extensively in examples (line 113: `"instruction": "The guard captain returns with reinforcements."`)
- Eval scenario gm_beat_lifecycle.py expects narration to reflect "gm_beat instruction" specifically — needs updating to check for type-aware narration instead
- Universal asserts check_pending_gm_beat_consumed and lifecycle_respected may need review if beat structure changes affect assertion logic
- Pre-existing: `tests/test_schema.py` imports `ProgressExtractResult` which no longer exists in `ccya/models.py` (renamed to `StorytellerResult`). Step 4.1 must fix this import and class reference. The validation command `pytest tests/test_schema.py::TestProgressExtractResult` will fail on import until this is fixed.
- Pre-existing: `tests/test_render.py` calls `_render(jinja_env, "extract_progress_user.j2", ...)` but this template doesn't exist (renamed to `storytell_user.j2`). Step 4.2 must fix the template name in those test calls, not just the test data.

---

## Implementation — Phase 1: Model schema simplification

### Context files to load
- `ccya/models.py` (lines 425-500)
- `docs/architecture/OVERVIEW.md` (state shape + GMBeat section)
- `docs/architecture/step2c-progress.md` (GMBeat schema + lifecycle sections)

### Detailed steps

#### Step 1.1 — Remove instruction field from GMBeat model

**File:** `ccya/models.py`

**What:** Delete the following:
- The `_GM_BEAT_FILLER_PREFIXES` constant tuple (lines 430-443)
- The `instruction: str | None = None` field from class GMBeat (line 466)
- The entire `_validate_instruction_quality` validator method on GMBeat (lines 469-480)

**Why:** The instruction field is being removed entirely. Without it, there's no validation to perform on it either. Keeping dead constants violates AGENTS.md clean code rules ("no dead config keys", "remove dead code immediately").

**Validation:** `python -c "from ccya.models import GMBeat; print(list(GMBeat.model_fields.keys()))"` — should show only `type`, `surface_as`, `beat_expires_turn`.

#### Step 1.2 — Update StorytellerResult._nullify_invalid_gm_beat validator

**File:** `ccya/models.py`

**What:** In StorytellerResult._nullify_invalid_gm_beat (line 497), change the condition from checking both instruction AND type to only checking for type presence. Remove the `not self.gm_beat.instruction or` part of the check so it reads:
```python
if not self.gm_beat.type:
    self.gm_beat = None
```

**Why:** Storytell no longer emits instruction, so requiring it would nullify all beats. Only type is needed as a validity gate — if there's no beat type, there's nothing to narrate.

**Validation:** `python -c "from ccya.models import StorytellerResult; r = StorytellerResult(gm_beat={'type': 'complication', 'surface_as': 'ambient'}); print(r.gm_beat.type)"` — should output `complication`.

### Tests to write or update

- **tests/test_schema.py**: Update `test_nullifies_gm_beat_without_instruction` (line 502) → rename to reflect new behavior: gm_beat with only type is now valid. Remove assertion about instruction being required; assert beat IS preserved when only type is provided.
- **tests/test_schema.py**: Update `test_valid_gm_beat_preserved` (line 520) — remove instruction from test data, assert beat preserved with just `{type}`.

#### Step 1.3 — Update repomap GMBeat documentation

**File:** `docs/repomap.md`

**What:** In "Key models with non-obvious behavior" section (lines 134-136), replace GMBeat bullet: remove reference to `_validate_instruction_quality` and filler prefix checks. Update to note only type validation remains in StorytellerResult._nullify_invalid_gm_beat.

---

## Implementation — Phase 2: Prompt template updates

### Context files to load
- `ccya/prompts/narrate_user.j2` (lines 75-82, full file)
- `ccya/prompts/storytell_system.j2` (full file, focus lines 67-130)
- `ccya/prompts/storytell_user.j2` (lines 47-52)

### Detailed steps

#### Step 2.1 — Verify narrate_user.j2 already uses new format (no-op)

**File:** `ccya/prompts/narrate_user.j2`

**What:** The template was previously updated — no edit needed. The file already contains only the new Beat type + surface_as block (lines 75-82) and has no references to `instruction`, `beat_hint`, or `Beat Hint`. The Beat Hint section was removed in a prior change.

**Validation:** Read template — confirm zero references to "instruction", "beat_hint", or "Beat Hint" in the file. Confirm the Beat type block looks like:

```jinja2
{% if pending_beat and pending_beat.type %}

**Beat type:** {{ pending_beat.type | replace('_', ' ') | upper }} to surface as `{{ pending_beat.surface_as | default('ambient') }}`. Use this as creative guidance for the scene — integrate it naturally with pacing context and arc state. Do not recite beat metadata directly in narration.
{% endif %}
```

Template renders without error when `pending_beat` is None, partial dict, or complete dict with only type + surface_as.

#### Step 2.2 — Remove pending_beat section from storytell_user.j2

**File:** `ccya/prompts/storytell_user.j2`

**What:** Delete the entire gm_beat/pending_beat block (lines 47-52):
```jinja2
## gm_beat
{% if pending_beat -%}
## pending_beat (carried from previous turn — not yet surfaced)
Type: {{ pending_beat.type }} | Expires at turn: T{{ pending_beat.beat_expires_turn }}
Instruction: {{ pending_beat.instruction }}
{% endif %}
```

**Why:** Storytell no longer needs to see carried-over beat context. Beat decisions should be based on current extraction data (scene state, threads, pacing context, band) rather than what was narrated last turn. This simplifies the prompt and removes vestigial disposition context.

**Validation:** Template renders without error when `pending_beat` is None or absent from context dict.

#### Step 2.3 — Update storytell_system.j2 beat guidance examples + remove grounding rule

**File:** `ccya/prompts/storytell_system.j2`

**What:** In the GM Beat guidance section (lines 100-121):
1. Remove all references to `"instruction": "..."` in emit examples (line 113). Change example from:
   ```
   Emit as: {"type": "pressure", "surface_as": "npc_behavior", "instruction": "The guard captain returns with reinforcements."}
   ```
   To:
   ```
   Emit as: {"type": "pressure", "surface_as": "npc_behavior"}
   ```
2. Delete the entire "GM Beat Grounding Rule" section (lines 116-121) — it only constrained instruction content referencing named entities, which is no longer relevant since there's no instruction string to constrain.

**Why:** Storytell must emit valid JSON matching new GMBeat schema ({type, surface_as} only). The grounding rule was specifically about constraining what `instruction` could reference; without instruction, the constraint has no target. Beat type diversity and band-aligned selection rules remain relevant.

**Validation:** Read template file after edit — verify zero references to "instruction" in storytell_system.j2 content.

### Tests to write or update

- **tests/test_render.py**: Update `test_narrate_rules_outcome_and_beat` (line 284) — remove instruction from pending_beat context dict, change assertion from checking "**GM Beat:** A mysterious figure approaches." to checking for new format like "beat type" + surface_as guidance text.
- **tests/test_render.py**: Update line 171 in extract_progress test — remove `instruction` key from pending_beat mock data. Note: if "encounter" is not a valid GMBeat type literal, also update the type value to a valid one like "complication".

### REPOMAP updates required

No changes needed — prompt template file responsibilities are already documented correctly in repomap.

---

## Implementation — Phase 3: Turn lifecycle simplification + extraction context

### Context files to load
- `ccya/engine/turn.py` (lines 71-82, 500-543, 876-1109)
- `ccya/engine/extraction.py` (line 349)

### Detailed steps

#### Step 3.1 — Remove save/restore of pending_gm_beat around narration in turn.py

**File:** `ccya/engine/turn.py`

**What:** Delete the save/clear/restore block (lines 1052-1060):
```python
# Save beat before clearing so extraction pipeline can see it
_beat_before_narration = (state.get("meta") or {}).get("pending_gm_beat")

# Clear pending_gm_beat after narration consumed it
state.setdefault("meta", {})["pending_gm_beat"] = None

# === Extraction pipeline (3 streams) ===
# Restore beat so progress extractor sees it in prompt for disposition decision
if _beat_before_narration is not None:
    state.setdefault("meta", {})["pending_gm_beat"] = _beat_before_narration
```

Replace with just the clear + extraction pipeline marker (lines 1054-1063):
```python
# Clear pending_gm_beat after narration consumed it — not restored since beat_disposition was removed
state.setdefault("meta", {})["pending_gm_beat"] = None

# === Extraction pipeline (3 streams) ===
exp_ms = _avg_extract_ms(save_dir)
yield ("phase", {"phase": "extract_start", "expected_ms": exp_ms})
```

**Why:** The save/restore served `beat_disposition` which was already removed. Storytell no longer needs to see carried-over beat context (removed in Phase 2). Keeping this code is dead logic that creates confusion about beat lifecycle semantics.

**Validation:** `grep -n "beat_before_narration\|_beat_before" ccya/engine/turn.py` — should return zero matches after edit.

#### Step 3.2 — Remove pending_beat from extraction context in extraction.py

**File:** `ccya/engine/extraction.py`

**What:** Delete line 349:
```python
pending_beat = (state.get("meta") or {}).get("pending_gm_beat") or None
```
And remove any references to `pending_beat` in the extraction context building that feeds storytell_user.j2. Specifically check if `pending_beat` is passed as a template variable to `_build_storytell_messages()` or equivalent — remove it from there too.

**Why:** Storytell prompt no longer includes pending beat section (Phase 2). The extracted value serves no purpose and should be cleaned up per AGENTS.md "remove dead code immediately."

**Validation:** `grep -n "pending_beat" ccya/engine/extraction.py` — should return zero matches after edit.

#### Step 3.3 — Remove pending_beat parameter from _compute_pacing_context + beat_hint generation in turn.py

**File:** `ccya/engine/turn.py`

**What:** Make four changes:
1. In PacingContext class (lines 71-82): Delete the `beat_hint: str | None` field from line 74 and remove it from the `.neutral()` default on line 82.
2. In _compute_pacing_context() function (around lines 500-533): Remove the beat_hint generation block (lines 528-533) that reads pending_beat to create hint string:
    ```python
    # Determine beat_hint: suggest a type when there's a pending beat
    beat_hint = None
    if pending_beat and isinstance(pending_beat, dict) and pending_beat.get("type"):
        beat_type = pending_beat.get("type") or "pressure"
        surface_as = pending_beat.get("surface_as", "ambient")
        beat_hint = f"{beat_type} ({surface_as})"
    ```
3. In the _compute_pacing_context() call site (line 957): Remove `pending_beat=_pending_gm_beat` from the function arguments.
4. Remove the `pending_beat` parameter from the `_compute_pacing_context()` function definition (line 506) and its docstring — it's now unused after removing beat_hint generation and the call-site argument.

**Why:** Without save/restore around extraction, Storytell won't see carried-over beats anymore. beat_hint generation depended on pending_beat to create "type (surface_as)" strings for narration — but Beat Hint display in narrate_user.j2 is now unreachable dead code (Phase 2). Keeping this computation serves no purpose and should be cleaned up per AGENTS.md clean code rules.

**Validation:** `grep -n "beat_hint" ccya/engine/turn.py` — should return zero matches after edit. Verify PacingContext.neutral() still works: `python -c "from ccya.engine.turn import PacingContext; pc = PacingContext.neutral(); print(dir(pc))"` — should not include beat_hint.

### Tests to write or update

No new tests needed for lifecycle simplification — existing gm_beat_lifecycle integration test (tests/test_integration.py line 258) should still pass since beat replace/clear logic at lines 1099-1109 is unchanged and floor relief injection via beat_locked remains intact. The save/restore removal doesn't affect observable behavior, only internal state management during the turn pipeline.

### REPOMAP updates required

No changes needed — repomap already correctly describes extraction field routing in "Extraction field routing" section (line 126). PacingContext is documented in "Cross-module contracts" under arc thread lifecycle which doesn't need updating for beat_hint removal.

---

## Implementation — Phase 4: Test + eval scenario updates + verification

### Context files to load
- `tests/test_schema.py` (lines 502-528)
- `tests/test_render.py` (lines 171, 284-307)
- `evals/scenarios/gm_beat_lifecycle.py`

### Detailed steps

#### Step 4.1 — Update test_schema.py gm_beat tests

**File:** `tests/test_schema.py`

**What:** 
1. Fix the test import (line 24): Change `ProgressExtractResult` to `StorytellerResult` — the model was renamed and `ProgressExtractResult` no longer exists in `ccya/models.py`. Also rename the test class from `TestProgressExtractResult` to `TestStorytellerResult`.
2. Rename and update `test_nullifies_gm_beat_without_instruction` (line 502): Change to verify that a beat with only `{type}` is now valid (not nullified). Remove instruction from test data entirely. Assert result.gm_beat is NOT None when only type is provided.
3. Update `test_valid_gm_beat_preserved` (line 520): Remove the long instruction string from test data, assert beat preserved with just type + surface_as.

**Why:** Tests must reflect new GMBeat schema where only type is required for a valid beat. The import fix is a pre-existing issue — `ProgressExtractResult` was renamed to `StorytellerResult` in a prior refactor but the tests weren't updated.

**Validation:** Run tests: `python -m pytest tests/test_schema.py::TestStorytellerResult -v` — all three gm_beat tests should pass with updated assertions.

#### Step 4.2 — Update test_render.py mock data + assertions

**File:** `tests/test_render.py`

**What:** Fix pre-existing template name issue and remove `instruction` keys from pending_beat dicts:
- Fix tests that call `_render(jinja_env, "extract_progress_user.j2", ctx)` — change template name to `"storytell_user.j2"` (the template was renamed in a prior refactor; `extract_progress_user.j2` doesn't exist).
- Line 171: Change `"pending_beat": {"type": "encounter", "instruction": "...", "beat_expires_turn": 6}` to remove instruction key. Also update type value since "encounter" is not a valid GMBeat literal — use "complication".
- Lines 298-299 (test_narrate_rules_outcome_and_beat): Remove `instruction` from pending_beat context dict and change surface_as if needed to match valid literals. Update assertion on line ~307 from checking "**GM Beat:** A mysterious figure approaches." to checking for new format output containing "beat type" + surface_as guidance text (e.g., assert "BEAT TYPE: COMPLICATION TO SURFACE AS" in out or similar).

**Why:** Mock data must match new GMBeat schema without instruction field. Assertions must check rendered content matching updated template format from Phase 2 Step 2.1.

**Validation:** `python -m pytest tests/test_render.py::test_narrate_rules_outcome_and_beat -v` — should pass with updated assertion checking for "beat type" + surface_as in output.

#### Step 4.3 — Update gm_beat_lifecycle eval scenario expectations

**File:** `evals/scenarios/gm_beat_lifecycle.py`

**What:** In the turn at line 45 (phase="gm_beat_surface"), update expects list:
- Change `"narrate should reflect the gm_beat instruction"` to `"narrate should integrate beat type and surface_as context naturally"`.
- Remove reference to "beat_disposition no longer exists" from line 37 since save/restore is now also removed (redundant).

**Why:** Eval expectations must match new narration behavior — narrator uses beat metadata as creative guidance rather than reciting a pre-written instruction string.

**Validation:** Scenario file is syntactically valid Python: `python -c "from evals.scenarios.gm_beat_lifecycle import scenario; print(scenario.id)"` should output `gm_beat_lifecycle`.

### Tests to write or update

All test updates are covered in Steps 4.1-4.3 above. No new standalone tests needed — existing integration tests cover beat lifecycle behavior which is unchanged (replace/clear/expiry). Floor relief injection via beat_locked remains tested by momentum_high scenario if it exists.

#### Final verification step

**What:** Run lint + typecheck:
```bash
make check
```

**Why:** AGENTS.md requires `make check` as final step of last phase. Ensures all changes are syntactically correct and type-consistent across the codebase.

### REPOMAP updates required

No additional changes — repomap updates were covered in Phase 1 Step 1.3.

---

## Architecture doc updates required

### `docs/architecture/OVERVIEW.md`
- **Lines ~95** (PacingContext beat_hint): Remove `beat_hint: str | None    # suggested gm_beat type, or None` from PacingContext definition — field is deleted in Phase 3 Step 3.3.
- **Lines 107-108** (GMBeat schema in state shape table): Remove `instruction: str | None` row from GMBeat entry. Update to show only type + surface_as + beat_expires_turn fields.

### `docs/architecture/step2c-progress.md`
- **Line 54** (GMBeat schema in mermaid diagram): Remove `instruction: str (must be ≥40 chars...)` line from schema definition. Update to show only type + surface_as fields.
- **Phase 2 description** (line 64): Rewrite narration consumption section — remove "narrator integrates the beat's instruction into prose" and replace with "narrator uses beat metadata as creative guidance alongside pacing directive." Remove mention of restoring beat for storyteller disposition since save/restore is deleted.
- **Phase 3 description** (lines 66-69): Update to reflect that Storytell no longer receives pending beat context in its prompt — it decides beats based solely on current extraction data.

### `docs/architecture/step1-narrate.md`
- Check if diagram references `pending_gm_beat` as an input node (line 25). Update to reflect that pending beat is still consumed by narration but without instruction content — only type + surface_as metadata flows through. Beat Hint section should be removed from any flowchart elements since it's deleted in Phase 2 Step 2.1.

### `docs/architecture/pacing-context.md`
- **Line 10**: Remove `beat_hint: str | None    # suggested gm_beat type, or None` from the PacingContext schema.
- **Lines 46, 50, 68**: Remove `beat_hint` references from the flowchart nodes (e.g., `BL --> G1["gate = 'block_add'<br>beat_hint = 'breathing_room'"]` → `BL --> G1["gate = 'block_add'"]`).
- **Line 77**: Remove `beat_hint` from "Narrator template renders only directive and beat_hint".
- **Line 3**: Update description to remove beat_hint from the collapsed struct list.

### `docs/architecture/delta-validate.md`
- No changes needed — gm_beat exclusion from StateDelta is still correct (beat written directly to state.meta.pending_gm_beat).
