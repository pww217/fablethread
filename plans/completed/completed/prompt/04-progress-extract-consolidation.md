# Progress Extract Consolidation

## Status
`completed`

## Phases

1 phase: unified thread operations in Progress Extract output schema, PacingContext integration into inputs, beat_disposition removal from outputs, scene_pressure_this_turn field dropped from _ExtractionContext.

## Issue (North Star)

Progress Extract has 6+ independent operations (`scene_pressure_add/remove/update` + `advanced_threads/candidate_opportunity`) with overlapping semantics but different schemas and rules — the LLM must decide "is this a scene pressure or an arc thread?" for every tension event, creating massive prompt complexity (~300-500 tokens in system prompt alone). Beat_disposition output encodes information Python already has from state mutations. Stakes input is redundant noise since narration already encodes failure cost (confirmed removed in 01). The LLM wastes tokens reconciling competing signals instead of making clean decisions about what tension to advance, resolve, or create on any given turn.

## Solution (North Star)

Progress understands exactly 3 operations regardless of scope: `thread_advance` (increment progress on existing threads), `thread_resolve` (resolve a thread with resolution_state), `thread_add` (create new thread when gate allows). No more "scene_pressure vs arc_thread" decision tree — the LLM just says "advance these ids, resolve these ids, add this one if gate permits." Beat_disposition removed entirely — Python infers disposition from gm_beat presence in delta plus turn expiry logic on state.meta.pending_gm_beat. PacingContext replaces 3+ independent fields (`narration_directive`, `deescalate`, `narrative_velocity`) as a single struct input that the LLM consumes without reconciliation overhead. scene_pressure_this_turn dropped from _ExtractionContext since scene_pressure no longer exists on state.scene after 01's unified model.

## Firm decisions
1. Unified operations work regardless of scope — the LLM just says "advance these ids, resolve these ids, add this one if gate allows" without deciding whether a tension is scene-scoped or arc-scoped (Python handles that via ArcThread.scope field). This eliminates the duplicate instruction sets in Progress's system prompt that explained separate rules for scene_pressure vs arc_threads.
2. Beat_disposition removed entirely — Python infers from gm_beat presence in delta plus turn expiry logic on state.meta.pending_gm_beat. No LLM output field needed for information the engine already has access to directly from state mutations.
3. PacingContext.gate == "allow" is the only condition under which Progress may emit thread_add; all other gate values block new threads regardless of LLM reasoning. This shifts a policy decision (should we allow new tension right now?) from the LLM into Python where the answer is already known via 02's PacingContext computation.
4. ThreadResolution model: `{id: str, resolution_state: Literal["resolved", "failed", "abandoned"]}` — the LLM emits a structured result for each resolved thread instead of free-text. This replaces `scene_pressure_remove` semantics (which was just IDs) with richer state tracking.
5. The old fields (`scene_pressure_add/remove/update`, `advanced_threads`, `candidate_opportunity`) are deleted from ProgressExtractResult in models.py — they will be replaced by the new unified operations. No backward compatibility needed since 01 already migrated all save file handling.

## Non-goals
- Changes to Scene Extract or State Extract prompts/templates (explicitly unchanged per design doc decision table)
- Narrator prompt changes (handled in 03)
- Delta application logic for unified thread signals (handled in 05 — _apply_thread_signals, _candidate_to_latent_thread, pressure.py lifecycle functions)
- Changes to PacingContext computation itself (already done in 02 — only the consumption of it by Progress changes here)

## Design Decisions Implemented From Plan Document
This phase implements the following decisions from `plans/narration-simplification-design.md`:
1. Remove scene_pressure[] → merge into unified arc.threads[] with scope: scene — eliminates duplicate instruction sets in Progress's system prompt that explained separate rules for scene_pressure vs arc_threads (300-500 tokens saved)
2. Remove beat_disposition from ProgressExtractResult — inferable from presence/absence of gm_beat output plus turn expiry in Python, not a decision the LLM needs to make
3. Collapse pacing signals into PacingContext for Progress inputs — replaces 6+ independent fields (narration_directive, deescalate, narrative_velocity) with single struct that the LLM consumes without reconciliation overhead
4. Gate thread_add via PacingContext.gate — prevents narrative escalation during de-escalation windows; structural constraint enforced by Python not left to LLM discretion
5. Progress Extract output schema after: 3 unified operations (thread_advance, thread_resolve, thread_add) replacing 6+ separate scene_pressure/thread operations

## Risks, Ambiguities, and Blockers
- **Ambiguity:** `_build_extraction_context()` drops `scene_pressure_this_turn` — does this affect any downstream logic that reads the ExtractionContext directly outside of Progress? Default: no other callers read _ExtractionContext fields beyond what's passed to Progress. Safe to remove.
- **Risk:** This is the largest prompt change (~300-500 tokens saved in system prompt, ~5 variables removed from user prompt). The unified thread instructions replace 2 parallel instruction sets (scene pressure + arc threads) with one — must verify the new unified schema covers all edge cases that were previously handled by scope-specific rules (e.g., scene-pressure urgency escalation at turn 3/5 thresholds now handled by Python age rules in 01, not LLM urgency labels). Delete tests for removed ProgressExtractResult fields (`scene_pressure_add/remove/update`, `beat_disposition`) rather than retrofitting them to pass unified thread operations.
- **Ambiguity:** `_apply_thread_signals()` currently reads `progress_result.advanced_threads` — after this phase it must read `thread_advance`. The function itself is NOT modified in 04 (that's 05), but the model field name changes mean 05 will need to update its references. This plan documents that handoff clearly for 05.
- **Blocker:** Phase 02 must complete first so PacingContext struct exists with `gate` field that this phase gates thread_add on. Phase 03 should be complete or near-complete since it updates the Narrate prompt — Progress prompts share context variables and we don't want conflicting changes.

## Dependencies
01: needs unified ArcThread shape in models + removed fields from ProgressExtractResult for the executor to implement against correct types. 02: needs PacingContext struct to exist so turn.py can pass it as a single input instead of 3+ separate signals. 03: should be complete or near-complete since Narrate prompt changes share context variable patterns with Progress prompts.

---

## Implementation — Phase 04: Progress Extract Consolidation

### Context files to load
The executor MUST read these files before making changes:

1. **`ccya/models.py`** (lines 491-534) — `ProgressExtractResult` class definition with fields to remove and new fields to add (`thread_advance`, `thread_resolve`, `thread_add`). Also need to define the new `ThreadResolution` model (~line 428 area, near ScenePressure).
2. **`ccya/prompts/extract_progress_system.j2`** (full file, 152 lines) — entire system prompt needs rewriting: remove scene_pressure instructions, beat_disposition tree, advanced_threads/candidate_opportunity sections; replace with unified thread operations + PacingContext guidance. Estimated ~300-500 tokens saved.
3. **`ccya/prompts/extract_progress_user.j2`** (full file, 109 lines) — remove `stakes`, `narrative_velocity`, `deescalation`, `narration_directive`, `scene_pressure` sections; replace with PacingContext display and unified threads list instead of active_threads/latent_threads split.
4. **`ccya/engine/extraction.py`** (lines 39-107, 326-400) — `_ExtractionContext` dataclass to drop `scene_pressure_this_turn`; `_build_extraction_context()` to stop populating it; `_extract_progress_messages()` signature and call site to replace old pacing variables with PacingContext.
5. **`ccya/engine/turn.py`** (lines 598-613) — the call to `_extract_progress_messages()` that passes `deescalate`, `narrative_velocity`, `stakes`, `narration_directive`, `resolved_pressures`. Replace with PacingContext struct.

### Detailed steps

#### Step 04.01 — Define ThreadResolution model and update ProgressExtractResult in models.py

**File:** `ccya/models.py`

**What:** 
1. Add a new `ThreadResolution` Pydantic model near the existing ScenePressure class (~line 428):
   - Fields: `id: str`, `resolution_state: Literal["resolved", "failed", "abandoned"]`
   
2. Replace the old fields in `ProgressExtractResult` (lines 491-502):
   - **DELETE:** `scene_pressure_add: list[ScenePressure]` 
   - **DELETE:** `scene_pressure_remove: list[str]`
   - **DELETE:** `scene_pressure_update: list[ScenePressure]`
   - **DELETE:** `advanced_threads: list[str]`
   - **DELETE:** `candidate_opportunity: str | None`
   - **KEEP (unchanged):** `recent_events_add`, `recent_events_update`, `recent_events_remove`, `actions`, `outcome_summary`, `gm_beat`
   
3. Add new fields to `ProgressExtractResult`:
   - `thread_advance: list[str] = Field(default_factory=list)` — snake_case thread IDs to increment progress on
   - `thread_resolve: list[ThreadResolution] = Field(default_factory=list)` — threads resolved with their resolution state
   - `thread_add: ArcThread | None = None` — new thread to create (null if gate != "allow" or no new tension warranted)

4. The existing validators (`_nullify_invalid_gm_beat`, `_coerce_actions`, `_warn_empty_actions`) remain unchanged on ProgressExtractResult. They operate on fields that are not being modified.

**Why:** This is the foundation type change. All downstream code (prompts, extraction context, turn.py call site) depends on these field names existing in the model. The ThreadResolution model provides structured resolution state instead of the old implicit semantics where `scene_pressure_remove` was just IDs and there was no "failed" or "abandoned" distinction for threads.

**Validation:** Run:
```python
from ccya.models import ProgressExtractResult, ThreadResolution
r = ProgressExtractResult(thread_advance=["t1"], thread_resolve=[{"id": "t2", "resolution_state": "resolved"}], gm_beat={"type": "pressure"})
print(r.model_dump(exclude_none=True))
```
Verify the output contains `thread_advance`, `thread_resolve`, `thread_add` (as null/absent), and does NOT contain any of the old fields.

#### Step 04.02 — Rewrite extract_progress_system.j2 for unified thread operations

**File:** `ccya/prompts/extract_progress_system.j2`

**What:** Complete rewrite of the system prompt. The new structure:

1. **Header (line 1):** Keep as-is, it's already generic enough.

2. **Output schema block (lines 3-20):** Replace with unified operations:
```json
{
  "recent_events_add": [],
  "recent_events_update": [],
  "recent_events_remove": [],
  "actions": [],
  "outcome_summary": "",
  "gm_beat": null,
  "thread_advance": ["thread_id_1", "thread_id_2"],
  "thread_resolve": [{"id": "thread_id", "resolution_state": "resolved"}],
  "thread_add": null
}
```

3. **Thread operations section (replaces lines 24-50):** One unified instruction set for all thread operations:
   - `thread_advance`: List of snake_case thread IDs meaningfully advanced this turn. Works regardless of scope — the LLM does NOT decide if a tension is "scene" or "arc". Python handles scoping via ArcThread.scope field. Include ONLY if events directly advanced that specific thread (same rules as old advanced_threads: meaningful action, not just mention/background presence).
   - `thread_resolve`: Threads fully resolved this turn. Each entry has an id and a resolution_state ("resolved" = tension addressed successfully, "failed" = tension escalated negatively, "abandoned" = player moved on without addressing it). This replaces both scene_pressure_remove (just IDs) AND advanced_threads semantics — if you resolve a thread by advancing it to completion, use thread_advance; if the turn ends the tension entirely, use thread_resolve.
   - `thread_add`: A new ArcThread object when a genuinely new story tension emerges this turn. CRITICAL: Only emit thread_add when PacingContext.gate shows "allow" — if gate is "block_add" or "block_escalate", do NOT add threads regardless of narrative context. The engine already decided the pacing doesn't support escalation. Thread must have: id (snake_case), summary, scope ("scene" for short-lived tension tied to current location/NPCs, "arc" for persistent story tension), urgency, tags (list).

4. **PacingContext guidance section (replaces lines 53-64):** Replace the old `narration_directive` guidance with PacingContext-based guidance:
   - Show how each directive maps to thread/beat decisions
   - Breathe → prefer breathing_room beat, do NOT add threads even if gate allows, resolve tensions where possible
   - Overwhelm → emit gm_beat of type pressure/escalation, may add scene-scoped threads if gate == "allow" 
   - Pressure → emit gm_beat of type complication/pressure, advance existing threads rather than adding new ones
   - Tension → do NOT add pressures unless concrete threat emerges; prefer advancing existing threads
   - Resolve a Threat → resolve resolved threads via thread_resolve with resolution_state="resolved"; do NOT add new threads
   - Combat Fatigue (secondary) → layer as thematic modifier on beat type, not a separate operation

5. **GM Beat section (lines 66-114):** Keep the GMBeat guidance largely intact but:
   - DELETE all references to `deescalate` values — they are no longer in context
   - DELETE all references to `narration_directive` as a standalone variable — use PacingContext.directive instead  
   - DELETE the entire `beat_disposition` section (lines 116-125) and its decision tree — Python infers disposition from gm_beat presence, no LLM output needed
   - Keep: band-aligned beat selection guidance, surface distribution rule, guidance per type/surface, GM Beat Grounding Rule

6. **Rules-outcome guidance (lines 142-145):** Keep as-is, already correct for unified thread operations.

7. **State-presence and output discipline rules:** Keep as-is.

**Why:** This is the single largest change — ~300-500 tokens saved in system prompt by removing duplicate instruction sets (scene_pressure lifecycle + arc_thread lifecycle = 2 separate rule books → 1 unified book). The LLM no longer needs to decide "is this a scene pressure or an arc thread?" — it just says what happened and Python handles scoping.

**Validation:** Read the resulting template. Verify:
- No references to `scene_pressure_add`, `scene_pressure_remove`, `scene_pressure_update` anywhere in text
- No reference to `beat_disposition` 
- No reference to `advanced_threads` or `candidate_opportunity` as field names (the concepts exist but under new names)
- PacingContext.gate gating is explicitly stated for thread_add
- Thread operations section covers both scope types without requiring LLM to distinguish them

#### Step 04.03 — Rewrite extract_progress_user.j2 for unified threads and PacingContext

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** Major restructuring of the user prompt template:

1. **NPC roster, location, conditions (lines 1-13):** Keep unchanged. These are extraction context fields that don't change.

2. **Threads section (replaces lines 15-31 active_threads/latent_threads split):** Replace the two separate sections with one unified threads list:
   - Show ALL threads from `all_threads` (both previously-active and latent) in a single section
   - Each thread shows: id, scope tag ([SCENE] or [ARC]), active status indicator, urgency, summary, tags, last_seen_turn if applicable
   - Group by scope for readability but present as one list
   - If no threads exist at all, show "None currently. Generate actions that could introduce new story directions."

3. **Recent events (lines 33-44):** Keep unchanged.

4. **Rules stakes section (lines 51-65): DELETE ENTIRELY.** The `stakes` field has been removed from IntentEnvelope in phase 01. This block references `{{ stakes }}`, `{{ band }}`, and emits scene_pressure_add instructions — all obsolete. Replace with a simpler band-aligned guidance that doesn't reference stakes:
   - Show the roll band (if present) as context for thread/beat decisions
   - crit_success/success → apply thread advancement freely, may add threads if gate allows
   - partial/setback/fail/crit_fail → do NOT mark threads as advanced for attempted action; prefer breathing_room/null beats on fail

5. **GM Beat / pending beat section (lines 66-71):** Keep unchanged — `pending_beat` is still in state.meta and relevant to Progress.

6. **Deescalation/narrative_velocity section (lines 72-88): DELETE ENTIRELY.** These variables (`narrative_velocity`, `resolved_pressures`) are being replaced by PacingContext. The deescalation logic was Python-computed; the LLM doesn't need to see raw velocity floats — it gets directive from PacingContext instead.

7. **Narration directive section (lines 89-93): DELETE ENTIRELY.** Replace with a single PacingContext display block:
   - Show `pacing_context.directive` if present and non-empty
   - Show `pacing_context.gate` value so the LLM knows whether thread_add is permitted ("allow" / "block_add" / "block_escalate")

8. **Current Pressures section (lines 94-98): DELETE ENTIRELY.** This shows `scene_pressure` from extraction_ctx which no longer exists after removing scene_pressure_this_turn. Thread state is now shown in the unified threads section above.

9. **Last turn narration, player intent, current turn narration (lines 99-109):** Keep unchanged.

**Why:** Removes ~5 variables from user prompt (`stakes`, `narrative_velocity`, `deescalation` block, `narration_directive`, `scene_pressure`) while adding PacingContext as a single structured input. The active_threads/latent_threads split becomes one unified list — the LLM sees all threads at once without needing to understand scope-based separation rules.

**Validation:** Read resulting template. Verify:
- No references to `stakes`, `narrative_velocity`, `deescalation` blocks, or `scene_pressure` 
- One unified threads section replaces active_threads + latent_threads split
- PacingContext fields are displayed (directive and gate)
- Band context remains for rules-outcome guidance

#### Step 04.04 — Drop scene_pressure_this_turn from _ExtractionContext in extraction.py

**File:** `ccya/engine/extraction.py`

**What:** 
1. Remove the `scene_pressure_this_turn: list[dict[str, Any]] = field(default_factory=list)` field and its docstring from `_ExtractionContext` dataclass (~line 52-53).
   
2. In `_build_extraction_context()` (~line 104), remove the line that populates it: `scene_pressure_this_turn=list(post_scene.get("scene_pressure") or [])`.

**Why:** scene_pressure no longer exists on state.scene after 01's unified model (it was migrated to arc.threads[] with scope=scene). The field is dead data — nothing reads it anymore since Progress Extract will use the unified threads list from state.arc.threads directly, not through extraction context. Removing it prevents confusion about whether scene_pressure still exists as a concept.

**Validation:** Run `grep -n 'scene_pressure_this_turn' ccya/engine/extraction.py` — should return zero matches. Also run `make check` to confirm no syntax errors or broken references.

#### Step 04.05 — Update _extract_progress_messages() signature and call site in extraction.py

**File:** `ccya/engine/extraction.py`

**What:** 
1. In `_extract_progress_messages()` function (~line 326-343), update the parameter list:
   - **DELETE:** `deescalate: float = 0.0`
   - **DELETE:** `narrative_velocity: float = 0.0`  
   - **DELETE:** `stakes: str = ""`
   - **DELETE:** `narration_directive: str = ""`
   - **DELETE:** `resolved_pressures: list[dict[str, Any]] | None = None`
   - **ADD:** `pacing_context: Any | None = None` (type is `Any` to avoid circular import of PacingContext from turn.py; the actual type is ccya.engine.turn.PacingContext)

2. In the template rendering context dict (~line 368-397), update what's passed to Jinja2:
   - **DELETE:** `"deescalate": deescalate,` 
   - **DELETE:** `"narrative_velocity": narrative_velocity,`
   - **DELETE:** `"stakes": stakes,`
   - **DELETE:** `"pending_beat": pending_beat,` — actually KEEP this, it's still needed for gm_beat context
   - **DELETE:** `"narration_directive": narration_directive,`
   - **DELETE:** `"resolved_pressures": resolved_pressures or [],`
   - **ADD:** `"pacing_context": pacing_context,`

3. The `active_threads` and `latent_threads` variables (~lines 349-357) are already computed from unified `arc.threads[]` with active bool filtering — they remain as-is for now since the user prompt template (step 04.03) will be updated to show them as a unified list.

**Why:** The function signature must match what turn.py passes and what the templates consume. Old variables (`deescalate`, `narrative_velocity`, `stakes`, etc.) are removed from both the Python interface AND the Jinja2 context — they no longer exist in the design after PacingContext consolidation.

**Validation:** Run `grep -n 'deescalate\|narrative_velocity\|stakes.*extract_progress\|resolved_pressures' ccya/engine/extraction.py` — should return zero matches for these as function parameters or template context keys (they may appear in comments). Also run `make check`.

#### Step 04.06 — Update _run_extraction_pipeline() call to _extract_progress_messages() in extraction.py

**File:** `ccya/engine/extraction.py` (~lines 598-613)

**What:** In the `_run_extraction_pipeline()` function, update the call site where Progress messages are built:
   - **DELETE:** `deescalate=deescalate,`
   - **DELETE:** `narrative_velocity=narrative_velocity,`
   - **DELETE:** `stakes="",`
   - **DELETE:** `band=_band,` — actually KEEP band for rules-outcome guidance in the prompt (the LLM needs to know roll outcome)
   - **DELETE:** `narration_directive=narration_directive,`
   - **DELETE:** `resolved_pressures=resolved_pressures,`
   - **ADD:** `pacing_context=pacing_context,`

**Wait — correction on band:** Looking at the design doc decision table, `band` is NOT listed as removed. The LLM still needs to know the roll outcome for rules-outcome guidance and beat selection. KEEP `band=_band`.

Also check: does `_run_extraction_pipeline()` have access to a PacingContext variable? It receives pacing signals from turn.py via parameters. Looking at line 598+, the function signature must be checked — it likely receives `deescalate`, `narrative_velocity`, etc. as parameters that need updating too.

**Why:** This is where the extraction pipeline actually calls _extract_progress_messages(). The call site must pass PacingContext instead of the old scattered variables, matching the new function signature from step 04.05.

**Validation:** Run `make check` to confirm syntax correctness and that all parameter names match between definition (step 04.05) and call site.

#### Step 04.07 — Update turn.py: pass PacingContext to _extract_progress_messages() instead of old variables

**File:** `ccya/engine/turn.py` (~lines 598-613 area where extraction pipeline is invoked, or wherever the run_turn orchestrator calls into extraction)

Actually, looking at the code flow more carefully: `_run_extraction_pipeline()` in extraction.py receives pacing signals as parameters from turn.py. The call happens around line ~700+ of turn.py (the `for evt in _run_extraction_pipeline(...)` loop). Let me check what parameters are passed to it.

**What:** In the run_turn() orchestrator, find where `_run_extraction_pipeline()` is called and update:
   - **DELETE:** passing `deescalate`, `narrative_velocity` as separate kwargs  
   - **ADD:** pass `pacing_context=_pc` (the PacingContext computed in step 02)

Also check if turn.py passes `stakes=""` to the extraction pipeline — this should be removed since stakes was deleted from IntentEnvelope.

**Why:** This is the top-level integration point where PacingContext flows from Python's pacing computation into Progress Extract's prompt building. Without this change, the old variables would still be passed and the new function signature (step 04.05) would reject them as unexpected kwargs.

**Validation:** Run `grep -n '_run_extraction_pipeline' ccya/engine/turn.py` to find all call sites. Verify each one passes PacingContext instead of deescalate/narrative_velocity/stakes. Run `make check`.

### Tests to write or update

Per AGENTS.md: "Tests are temporarily removed during refactor." No test changes needed for this phase. All tests will be addressed when the testing infrastructure returns. The following is documented for future reference:

**To delete (when tests return):**
- Any test asserting on `ProgressExtractResult.scene_pressure_add`, `scene_pressure_remove`, `scene_pressure_update` fields — these no longer exist
- Any test asserting on `ProgressExtractResult.beat_disposition` field — removed in this phase  
- Any test asserting on `ProgressExtractResult.advanced_threads` or `candidate_opportunity` — replaced by unified operations
- Any test passing `deescalate`, `narrative_velocity`, `stakes`, `resolved_pressures` to `_extract_progress_messages()` — signature changed

**To write (when tests return):**
- `test_thread_resolution_model_serialization`: Verify ThreadResolution serializes with id and resolution_state fields only
- `test_progress_extract_result_unified_operations`: Create ProgressExtractResult with thread_advance, thread_resolve, thread_add; verify old fields are absent from model_dump()
- `test_extract_progress_messages_receives_pacing_context`: Call _extract_progress_messages(pacing_context=...) and verify template context contains pacing_context directive/gate but NOT deescalate/narrative_velocity/stakes
- `test_extraction_context_no_scene_pressure_this_turn`: Verify _ExtractionContext has no scene_pressure_this_turn field after removal

### REPOMAP updates required

Update `docs/repomap.md` with the following changes:

1. **Cross-module contracts — Extraction field routing (~line 114):** Update ProgressExtractResult entry to show new unified operations instead of old fields:
   - OLD: `advanced_threads, candidate_opportunity, recent_events_add/update/remove, actions, outcome_summary, scene_pressure_add/remove/update, gm_beat, beat_disposition`
   - NEW: `thread_advance, thread_resolve (list[ThreadResolution]), thread_add (ArcThread | None), recent_events_add/update/remove, actions, outcome_summary, gm_beat`

2. **5-call turn pipeline section (~line 88):** Update Progress Extract description to reflect unified operations and PacingContext input instead of separate pacing signals:
   - OLD: "advanced_threads, candidate_opportunity, recent_events, actions, gm_beat, scene_pressure"  
   - NEW: "thread_advance, thread_resolve, thread_add (gated by PacingContext.gate), recent_events, actions, gm_beat"

3. **Key models (~line 120):** Add ThreadResolution to the type aliases or key models section if one exists for Pydantic models.
