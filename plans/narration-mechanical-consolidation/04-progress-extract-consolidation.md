# Progress Extract Consolidation

## Status
`open`

## Phases

1 phase: unified thread operations in Progress Extract output schema, PacingContext integration into inputs, beat_disposition removal from outputs, scene_pressure_this_turn field dropped from _ExtractionContext.

## Issue (North Star)

Progress Extract has 6+ independent operations (scene_pressure_add/remove/update + advanced_threads/candidate_opportunity) with overlapping semantics but different schemas and rules — the LLM must decide "is this a scene pressure or an arc thread?" for every tension event, creating massive prompt complexity (~300-500 tokens in system prompt alone). Beat_disposition output encodes information Python already has from state mutations. Stakes input is redundant noise since narration already encodes failure cost (confirmed removed in 01). The LLM wastes tokens reconciling competing signals instead of making clean decisions about what tension to advance, resolve, or create on any given turn.

## Solution (North Star)

Progress understands exactly 3 operations regardless of scope: `thread_advance` (increment progress on existing threads), `thread_resolve` (resolve a thread with resolution_state), `thread_add` (create new thread when gate allows). No more "scene_pressure vs arc_thread" decision tree — the LLM just says "advance these ids, resolve these ids, add this one if gate permits." Beat_disposition removed entirely — Python infers disposition from gm_beat presence in delta plus turn expiry logic on state.meta.pending_gm_beat. PacingContext replaces 3+ independent fields (narration_directive, deescalate, narrative_velocity) as a single struct input that the LLM consumes without reconciliation overhead. scene_pressure_this_turn dropped from _ExtractionContext since scene_pressure no longer exists on state.scene after 01's unified model.

## Firm decisions
1. Unified operations work regardless of scope — the LLM just says "advance these ids, resolve these ids, add this one if gate allows" without deciding whether a tension is scene-scoped or arc-scoped (Python handles that via ArcThread.scope field). This eliminates the duplicate instruction sets in Progress's system prompt that explained separate rules for scene_pressure vs arc_threads.
2. Beat_disposition removed entirely — Python infers from gm_beat presence in delta plus turn expiry logic on state.meta.pending_gm_beat. No LLM output field needed for information the engine already has access to directly from state mutations.
3. PacingContext.gate == "allow" is the only condition under which Progress may emit thread_add; all other gate values block new threads regardless of LLM reasoning. This shifts a policy decision (should we allow new tension right now?) from the LLM into Python where the answer is already known via 02's PacingContext computation.

## Non-goals
- Changes to Scene Extract or State Extract prompts/templates (explicitly unchanged per design doc decision table)
- Narrator prompt changes (handled in 03)
- Delta application logic for unified thread signals (handled in 05)

## Design Decisions Implemented From Plan Document
This phase implements the following decisions from `plans/narration-simplification-design.md`:
1. Remove scene_pressure[] → merge into unified arc.threads[] with scope: scene — eliminates duplicate instruction sets in Progress's system prompt that explained separate rules for scene_pressure vs arc_threads (300-500 tokens saved)
2. Remove beat_disposition from ProgressExtractResult — inferable from presence/absence of gm_beat output plus turn expiry in Python, not a decision the LLM needs to make
3. Collapse pacing signals into PacingContext for Progress inputs — replaces 6+ independent fields (narration_directive, deescalate, narrative_velocity) with single struct that the LLM consumes without reconciliation overhead
4. Gate thread_add via PacingContext.gate — prevents narrative escalation during de-escalation windows; structural constraint enforced by Python not left to LLM discretion
5. Progress Extract output schema after: 3 unified operations (thread_advance, thread_resolve, thread_add) replacing 6+ separate scene_pressure/thread operations

## Risks, Ambiguities, and Blockers
- **Ambiguity:** `_build_extraction_context()` drops scene_pressure_this_turn — does this affect any downstream logic that reads the ExtractionContext directly outside of Progress? Default: no other callers read _ExtractionContext fields beyond what's passed to Progress.
- **Risk:** This is the largest prompt change (~300-500 tokens saved in system prompt, ~5 variables removed from user prompt). The unified thread instructions replace 2 parallel instruction sets (scene pressure + arc threads) with one — must verify the new unified schema covers all edge cases that were previously handled by scope-specific rules (e.g., scene-pressure urgency escalation at turn 3/5 thresholds now handled by Python age rules in 01, not LLM urgency labels). Delete tests for removed ProgressExtractResult fields (scene_pressure_add/remove/update, beat_disposition) rather than retrofitting them to pass unified thread operations.

## Dependencies
01: needs unified ArcThread shape in models + removed fields from ProgressExtractResult for the executor to implement against correct types. 02: needs PacingContext struct to exist so turn.py can pass it as a single input instead of 3+ separate signals.
