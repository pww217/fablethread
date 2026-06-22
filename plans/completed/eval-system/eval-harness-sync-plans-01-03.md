# eval-harness-sync-plans-01-03

## Status
`completed`

## Phases

3 phases: Update all rubric directive references to new values, add auto-checker assertions for Plans 01-03 mechanics (ArcThread.key dedup, consecutive_pressure_turns tracking, beat_locked dual-trigger), strengthen directive rendering check + metrics table + engine mirror constants.

## Issue
The eval harness still references the OLD directive value set ("MoveOn", "Escalate") from before Plan #03 pacing overhaul across all 3 rubric files (`default.md`, `narrative_interplay.md`, `meta.md`). There are no auto-checker assertions for any new mechanics introduced by Plans 01-03: ArcThread.key dedup gate, consecutive_pressure_turns tracking, beat_locked dual-trigger condition. The directive rendering check uses loose substring matching ("Pressure" matches "Scene Pressure") so it can't validate the SPECIFIC directive value rendered into prompts. Judge metrics table lacks pacing-relevant columns (directive per turn, beat_locked status). Engine mirror constants_block is missing new config (`consecutive_pressure_threshold`). This means every judge evaluation pass evaluates against an obsolete value set and no auto-checker catches mechanical bugs in Plans 01-03 implementations.

## Solution
Three phases grouped by concern: Phase 01 updates all 3 rubric files to the new 9-value directive palette ("Breathe", "Scene Imperative", "Overwhelm", "Resolve a Threat", "Pressure", "Tension", "Threat Pressure", "Scene Pressure", "") and adds complete beat-type mappings for every new directive. Phase 02 adds 5 universal assertions to `universal_asserts.py` (ArcThread.key dedup validation, consecutive_pressure_turns tracking, beat_locked dual-trigger condition, negative assertion for removed directives, negative assertion for removed NPC states). Phase 03 strengthens `check_narration_directive_rendered` to validate exact pacing_ctx directive match vs rendered prompts, adds pacing columns to judge metrics table (`pacing_directive`, `beat_generated`, `beat_consumed`), and exposes new config constants in engine_mirror.py.

## Firm decisions
1. The 9 valid PacingContext.directive values are: "", "Breathe", "Scene Imperative", "Overwhelm", "Resolve a Threat", "Pressure", "Tension", "Threat Pressure", "Scene Pressure" (may include "; Resolve a Threat" secondary when beat_locked). This is the canonical set for all rubric/assertion updates.
2. `check_narration_directive_rendered` will validate that pacing_ctx.directive value matches what appears in rendered prompts using structured field comparison, not just substring presence of any known directive string.
3. New assertions follow existing universal_asserts.py patterns: return dict with keys `{passed: bool, detail: str}` and use yellow severity for informational warnings.

## Non-goals
- Do NOT modify judge rubric scoring weights or section structures — only update directive value references to match new palette.
- Do NOT add tests (tests are temporarily removed during refactor per AGENTS.md).
- Do NOT change the pacing_context event schema (`directive`, `beat_locked`, `gate`, `summary` fields remain unchanged).

## Risks, Ambiguities, and Blockers
1. **Directive value exactness**: The directive may include a secondary "; Resolve a Threat" suffix when beat_locked is True. Assertions must handle both the base value ("Pressure") and the suffixed value ("Pressure; Resolve a Threat").
2. **Event data availability for ArcThread.key dedup assertion**: Need to verify whether `state_snapshot.arc.threads` per turn event includes the `.key` field so assertions can check that no two threads have similar non-null keys. If key is not persisted in state snapshots, this assertion will need to read from a different source or be skipped.
3. **consecutive_pressure_turns availability**: The counter is stored in `state["meta"]["consecutive_pressure_turns"]` at turn end — must verify it's included in the event's meta section for auto-checker access.

## Implementation — Phase 01: Rubric directive value updates

### Context files to load
- `evals/rubrics/default.md` (Section 4B line ~253)
- `evals/rubrics/narrative_interplay.md` (Sections 1A.5 line ~64, 1B.5 line ~81)
- `evals/rubrics/meta.md` (Section 2 line ~52)

### Detailed steps

#### Step 01.1 — Update default.md directive value references

**File:** `evals/rubrics/default.md`

**What:** Replace the stale directive value list `(directive values: "", "Breathe", "Pressure", "MoveOn", "Escalate")` at line ~253 with the new 9-value set. Update any prose that references old directives ("MoveOn" → no direct replacement, it was removed; "Escalate" → "Overwhelm").

**Why:** Judges evaluating Section 4B will misclassify or fail to recognize new directive values ("Scene Imperative", "Scene Pressure", etc.) if the rubric only lists 5 old directives. This causes every judge evaluation pass to use an obsolete value set.

**Validation:** `rg -n '"MoveOn"|"Escalate"' evals/rubrics/default.md` should return no matches after this step.

#### Step 01.2 — Update narrative_interplay.md directive values and beat-type mappings

**File:** `evals/rubrics/narrative_interplay.md`

**What:** 
- Line ~64: Replace stale directive value list with new 9-value set
- Lines ~78-86 (Section 1B.5): Rewrite the rule-based beat type mapping to cover ALL 9 directives:
  - `""` → none/no beat expected
  - `"Breathe"` → breathing_room
  - `"Scene Imperative"` → revelation or escalation (strong scene-level signal)
  - `"Overwhelm"` → complication (more severe than Pressure, short-circuits all other directives)
  - `"Resolve a Threat"` → resolution guidance for aged-out threats
  - `"Pressure"` / `"Threat Pressure"` → complication
  - `"Tension"` → mild escalation or none
  - `"Scene Pressure"` → mild scene-level pressure (append to directive when effective_age >= 3)

**Why:** The beat-type mapping is the judge's structured baseline for evaluating whether GM beats are appropriate. Without mappings for new directives, judges fall back entirely to subjective LLM judgment rather than having any rule-based evaluation criteria.

**Validation:** `rg -n '"MoveOn"|"Escalate"' evals/rubrics/narrative_interplay.md` should return no matches after this step. Verify all 9 directive values appear in the beat-type mapping section.

#### Step 01.3 — Update meta.md directive value references

**File:** `evals/rubrics/meta.md`

**What:** Replace `(PacingContext.directive values (" | "Breathe" | "Pressure" | "MoveOn" | "Escalate")` at line ~52 with the new 9-value set. Update any cross-judge contradiction checks that reference old directives.

**Why:** The meta judge evaluates contradictions between domain judges. If it only knows about 5 old directive values, it will miss or misclassify contradictions involving new directives ("Scene Imperative", "Overwhelm", etc.).

**Validation:** `rg -n '"MoveOn"|"Escalate"' evals/rubrics/meta.md` should return no matches after this step.

### Tests to write or update
None (tests temporarily removed per AGENTS.md).

### REPOMAP updates required
- None needed — rubric files are not in the source module index; they're external evaluation resources.

## Implementation — Phase 02: Universal assertions for Plans 01-03 mechanics

### Context files to load
- `ccya/eval/universal_asserts.py` (full file, especially existing assertion patterns and run_all_universal_asserts at line ~728)
- `ccya/engine/turn.py` lines 596-640 (_merge_arc_update fuzzy dedup gate logic), lines 1430-1460 (consecutive pressure counter two-pass update, beat_locked dual-trigger logic)

### Detailed steps

#### Step 02.1 — Add check_arcthread_key_dedup assertion

**File:** `ccya/eval/universal_asserts.py`

**What:** New function `check_arcthread_key_dedup(event: dict[str, Any]) -> dict[str, Any]` that validates the ArcThread.key auto-merge dedup gate works correctly. Logic:
1. Read `state_snapshot.arc.threads[]` from event
2. Filter to threads where `.key` is not None and not empty string
3. For every pair of threads with non-null keys, compute token-overlap similarity (same algorithm as turn.py fuzzy merge — 70% threshold)
4. If any two threads have similar keys above 70%, fail the assertion: "Duplicate ArcThread.key detected"
5. Pass if no duplicates found or fewer than 2 threads with non-null keys

**Why:** Plan #02 added auto-merge dedup gate at thread_add point using token-overlap scoring with 70% threshold. There is NO universal assertion that validates this behavior works correctly — duplicate threads could silently get re-processed every turn, wasting tokens and confusing pacing logic.

**Validation:** Function signature must match existing pattern: `(event) -> dict` returning `{passed: bool, detail: str}`. Add to `run_all_universal_asserts` function call list at the end of the file.

#### Step 02.2 — Add check_consecutive_pressure_tracking assertion

**File:** `ccya/eval/universal_asserts.py`

**What:** New function `check_consecutive_pressure_tracking(event: dict[str, Any], prev_event: dict | None = None) -> dict[str, Any]` that validates the two-pass consecutive pressure counter works correctly. Logic:
1. Read `pacing_context.directive` from event (base value without "; Resolve a Threat" suffix if present)
2. Check whether any thread_advance occurred in this turn's extraction results (`event.get("extraction", {}).get("storytell", {}).get("thread_advance")`)
3. If directive was "Pressure" or "Overwhelm" AND no thread_advance: `consecutive_pressure_turns` should be >= 1 (or increment from prev_event value)
4. If any thread_advance occurred OR directive changed to non-pressure value: `consecutive_pressure_turns` should reset to 0
5. Read counter from event meta (`event.get("state_snapshot", {}).get("meta", {}).get("consecutive_pressure_turns")`) and validate it matches expected behavior

**Why:** Plan #03 added a two-pass end-of-turn consecutive pressure counter that increments when directive was Pressure/Overwhelm AND no thread_advance occurred. There is NO assertion validating the counter actually increments correctly or resets properly — a bug in the two-pass logic would go undetected, defeating the core purpose of detecting stuck-player loops.

**Validation:** Function signature must match existing pattern with optional prev_event: `(event, prev_event | None = None) -> dict` returning `{passed: bool, detail: str}`. Add to `run_all_universal_asserts` call list.

#### Step 02.3 — Add check_beat_locked_dual_trigger assertion

**File:** `ccya/eval/universal_asserts.py`

**What:** New function `check_beat_locked_dual_trigger(event: dict[str, Any], prev_event: dict | None = None) -> dict[str, Any]` that validates the dual-trigger beat_locked condition works correctly. Logic:
1. Read `pacing_context.beat_locked` from event (should be True when either trigger fires)
2. Read `state_snapshot.meta.momentum` and compare to config floor (-3 default). If momentum <= -3, beat_locked should be True.
3. Read `consecutive_pressure_turns` from meta section. If >= 3 (config threshold), beat_locked should be True even if momentum > -3.
4. Assert: `beat_locked == (momentum <= config.momentum_floor or consecutive_pressure_turns >= config.consecutive_pressure_threshold)`

**Why:** Plan #03 changed beat_locked from single-trigger (`momentum <= config.momentum_floor`) to dual-trigger OR condition. There is NO assertion that validates the new condition fires when consecutive pressure threshold is reached even if momentum is NOT at floor — if only the old check works, the relief mechanism won't fire for stuck players receiving repeated Pressure directives without thread advancement.

**Validation:** Function signature matches existing pattern with optional prev_event: `(event, prev_event | None = None) -> dict` returning `{passed: bool, detail: str}`. Add to `run_all_universal_asserts` call list.

#### Step 02.4 — Add check_no_removed_directives assertion (negative assertion)

**File:** `ccya/eval/universal_asserts.py`

**What:** New function `check_no_removed_directives(event: dict[str, Any]) -> dict[str, Any]` that validates removed directives ("Location Pressure", "Location Imperative", "Combat Fatigue") do NOT appear in any rendered prompts or pacing context outputs. Logic:
1. Read `narrate_prompt.rendered_user` and `extraction.storytell.rendered_user` from event
2. Check both strings for case-insensitive presence of "location pressure", "location imperative", or "combat fatigue"
3. If any found, fail with yellow severity detail listing which directive was found in which prompt

**Why:** While the engine won't produce these directives after Plans 01-03, having a negative assertion catches template drift or accidental re-introduction during future edits — useful safety check to prevent regression.

**Validation:** Function signature matches existing pattern: `(event) -> dict` returning `{passed: bool, detail: str}` with yellow severity for informational warnings. Add to `run_all_universal_asserts` call list.

#### Step 02.5 — Add check_no_removed_npc_states assertion (negative assertion)

**File:** `ccya/eval/universal_asserts.py`

**What:** New function `check_no_removed_npc_states(event: dict[str, Any]) -> dict[str, Any]` that validates removed NPC states ("JUST_LEFT", "recently_left") do NOT appear in state snapshots or scene extractor outputs. Logic:
1. Read `state_snapshot.scene` from event and check for presence of `recently_left` key — if present, fail assertion
2. Check any NPC roster data (`narrate_prompt.rendered_user`) for case-insensitive "JUST_LEFT" string — if found, fail with yellow severity detail

**Why:** Plan #01 removed scene.recently_left, scene.recently_left_turns, and JUST_LEFT presence tag from the entire codebase. A negative assertion catches any accidental re-introduction or stale data leaking into events.

**Validation:** Function signature matches existing pattern: `(event) -> dict` returning `{passed: bool, detail: str}` with yellow severity for informational warnings. Add to `run_all_universal_asserts` call list.

### Tests to write or update
None (tests temporarily removed per AGENTS.md).

### REPOMAP updates required
- Update `ccya/eval/universal_asserts.py` entry in module index table to reflect 20 auto-checkers instead of 15 ("+ check_arcthread_key_dedup, + check_consecutive_pressure_tracking, + check_beat_locked_dual_trigger, + check_no_removed_directives, + check_no_removed_npc_states")

## Implementation — Phase 03: Directive rendering check + metrics table + engine mirror constants

### Context files to load
- `ccya/eval/universal_asserts.py` lines 666-709 (`check_narration_directive_rendered`)
- `ccya/eval/judge.py` lines 698-731 (`_render_deterministic_signals`), 734-763 (`_build_metrics_rows`)
- `ccya/eval/engine_mirror.py` full file (constants_block function at line ~72)

### Detailed steps

#### Step 03.1 — Strengthen check_narration_directive_rendered to validate exact directive match

**File:** `ccya/eval/universal_asserts.py` lines 666-709 (`check_narration_directive_rendered`)

**What:** Rewrite the function to validate that the SPECIFIC pacing_ctx.directive value matches what appears in rendered prompts, not just any known directive substring. Logic:
1. Read `pacing_context.directive` from event's structured data (the engine-computed value)
2. If pacing_context is missing or empty → pass with detail "no pacing context found"
3. Extract the base directive value by stripping "; Resolve a Threat" suffix if present
4. Check that this exact base value appears in `narrate_prompt.rendered_user` (case-insensitive check for `"directive: {value}"` pattern)
5. If base value NOT found in narrate prompt → fail with detail showing expected vs actual
6. Also check storytell rendered_user contains the directive — if present in narrate but absent from storytell, fail with yellow severity

**Why:** Current logic only checks substring presence of any known directive ("Pressure" matches "Scene Pressure") so it can't distinguish which specific directive was rendered. This causes false positives where the assertion passes even when the wrong directive value appears in prompts. The new logic validates exact match between pacing_ctx.directive and rendered prompt content using structured field comparison rather than loose substring matching.

**Validation:** `rg -n '"directive:"' ccya/eval/universal_asserts.py` to verify the function now checks for `"directive: {value}"` pattern with specific value from pacing_context. Run `make check` to ensure lint + typecheck pass.

#### Step 03.2 — Add pacing columns to judge metrics table

**File:** `ccya/eval/judge.py` lines 734-763 (`_build_metrics_rows`)

**What:** Extend the row dict in `_build_metrics_rows` to include three new pacing-relevant fields:
1. `"pacing_directive"` — extracted from `event.get("pacing_context", {}).get("directive", "")` per turn event
2. `"beat_generated"` — boolean, True if `state_snapshot.meta.pending_gm_beat` is non-empty dict in this turn's state snapshot
3. `"beat_consumed"` — boolean, True if beat was consumed (pending_gm_beat present in prev_event but not current)

**Why:** The judge metrics table currently only shows momentum_after as the single pacing-related column. Without directive value per turn and beat lifecycle status, judges cannot evaluate whether directives were changing appropriately or whether beat_locked was firing at the right times — that data isn't captured for evaluation.

**Validation:** After this step, every row in `_build_metrics_rows` output should have keys: `turn`, `ruling_tok_in`, `narrate_tok_in`, `scene_tok_in`, `state_tok_in`, `storytell_tok_in`, `parse_failures`, `retries`, `momentum_after`, `pacing_directive`, `beat_generated`, `beat_consumed`.

#### Step 03.3 — Expose new config constants in engine_mirror.py

**File:** `ccya/eval/engine_mirror.py` lines 72-90 (`constants_block`)

**What:** Add two new constant references to the `constants_block()` function's returned string:
1. `"Consecutive pressure threshold"` — value from `config.consecutive_pressure_threshold` (default 3). Import from config module or use hardcoded default if config not available at mirror level.
2. `"Effective scene age combat boost"` — "+2 when 'combat' in scene tags" description to explain the pacing context logic

**Why:** Judges reason about engine behavior but don't know what the consecutive pressure threshold is or that combat scenes get a +2 effective_age boost. This makes it harder for judges to correctly evaluate whether pacing mechanics behaved as designed. The constants_block provides live engine config to judge traces so they can validate against actual values rather than guessing.

**Validation:** `rg -n "consecutive_pressure|combat.*boost" ccya/eval/engine_mirror.py` should show the new entries in constants_block output. Run `make check` to ensure lint + typecheck pass.

### Tests to write or update
None (tests temporarily removed per AGENTS.md).

### REPOMAP updates required
- Update `ccya/eval/judge.py` entry in module index table to note `_build_metrics_rows` now includes pacing_directive, beat_generated, beat_consumed columns
- Update `ccya/eval/engine_mirror.py` entry to note constants_block exports consecutive_pressure_threshold and effective_scene_age combat boost
