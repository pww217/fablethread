---
name: Cleanup pass after pipeline-remediation Plans A–D
overview: ""
todos:
  - id: phase-01
    content: Phase 01 — comment out token-budget ceilings + TestTokenBudgetCeilings in tests/test_engine_pipeline.py
    status: pending
  - id: phase-02
    content: Phase 02 — remove `failed`/`last_turn_failed` plumbing across extraction.py, turn.py (both run_turn + run_turn_retry), narrate.py, narrate_user.j2, and 4 test files
    status: pending
  - id: phase-03
    content: Phase 03 — drop dead quest_ages loop in extract_progress_user.j2; trim recent_turns slice to [-1:] for scene call in extraction.py
    status: pending
  - id: phase-04
    content: Phase 04 — rewrite _SCENE/_STATE/_PROGRESS_RESPONSE fixtures + _state_response() helper to match post-Plan-A schema
    status: pending
  - id: phase-05
    content: Phase 05 — narration markers alignment (BLOCKED on owner picking option a or b)
    status: pending
  - id: phase-06
    content: Phase 06 — ARCHITECTURE.md (Step 2a/2b/2c, Delta Merge, Cross-Pipeline arrows), REPOMAP/{state,engine,testing}.md, 4 plan-doc pointer fixes, TODO.md updates, final grep sweep
    status: pending
  - id: extract-to-files
    content: "When approved: extract phases into docs/plans/four-plans-cleanup/01-...md through 06-...md per project plan-folder convention"
    status: pending
isProject: false
---

# Cleanup pass after pipeline-remediation Plans A–D

## Status
`open`

## Part of
`docs/plans/four-plans-cleanup/` (effort folder created by phase 01; this plan replaces the previous draft cleanup plan).

## Dependencies
Plans A, B, C, D under `docs/plans/eval-results-remediation/` must be merged. None of the listed eval-engine remediation work (planned next, separate effort) is a dependency or blocker for any phase here.

## Objective
After Plans A/B/C/D landed, the engine, prompts, tests, and docs contain leftover stale references, dead code paths, and stale architecture diagrams. This plan removes them and aligns the documentation so the next eval-engine refactor has a clean substrate to plan against. No behavior change is intended for any LLM-driven path; this is a hygiene pass.

## Non-goals
- Does NOT touch any file under `ccya/ccya/eval/*`, `evals/*`, `evals/runs/*`, or `evals/rubrics/*`. These are owned by the eval-engine update planned next.
- Does NOT add new product features, prompts, or model fields.
- Does NOT change pipeline behavior, ordering, retry counts, gating, dedup logic, or pressure rules.
- Does NOT reintroduce token-budget ceilings under any form (tests are commented out, never deleted, so they can be revisited).
- Does NOT rewrite or rename the four plan documents under `docs/plans/eval-results-remediation/`. Only their stale REPOMAP pointers are corrected.

## Affected files
| File | Change type | Summary of change |
|---|---|---|
| `ccya/docs/plans/four-plans-cleanup/01-remove-token-budget-tests.md` | create | Phase 01 plan doc (extracted from this spec) |
| `ccya/docs/plans/four-plans-cleanup/02-remove-failed-plumbing.md` | create | Phase 02 plan doc |
| `ccya/docs/plans/four-plans-cleanup/03-prompt-and-extraction-cleanup.md` | create | Phase 03 plan doc |
| `ccya/docs/plans/four-plans-cleanup/04-test-fixtures-cleanup.md` | create | Phase 04 plan doc |
| `ccya/docs/plans/four-plans-cleanup/05-narration-markers-alignment.md` | create | Phase 05 plan doc |
| `ccya/docs/plans/four-plans-cleanup/06-architecture-and-repomap-update.md` | create | Phase 06 plan doc |
| `ccya/tests/test_engine_pipeline.py` | modify | Phase 01: comment out token-budget ceilings + tests |
| `ccya/ccya/engine/turn.py` | modify | Phase 02: remove `failed`/`last_turn_failed` plumbing in both `run_turn` and `run_turn_retry`; fix stale comment about progress vs scene gm_beat |
| `ccya/ccya/engine/extraction.py` | modify | Phase 02: drop `failed` from `_run_extraction_pipeline` return tuple + docstring; Phase 03: trim `recent_turns[-1:]` for scene call |
| `ccya/ccya/engine/narrate.py` | modify | Phase 02: drop `last_turn_failed` parameter and context key |
| `ccya/ccya/prompts/narrate_user.j2` | modify | Phase 02: drop `## last_turn_failed` block |
| `ccya/ccya/prompts/extract_progress_user.j2` | modify | Phase 03: drop dead `quest_ages` loop; Phase 05 (option a only): rename narration markers |
| `ccya/ccya/prompts/extract_scene_user.j2` | modify | Phase 05 (option a only): rename narration markers |
| `ccya/ccya/prompts/extract_state_user.j2` | modify | Phase 05 (option a only): rename narration markers |
| `ccya/docs/PROMPTING.md` | modify | Phase 05 (option b only): record `## CURRENT TURN NARRATION` as the extract convention |
| `ccya/tests/test_engine_smoke.py` | modify | Phase 02: drop `last_turn_failed` test cases + kwargs; Phase 04: rewrite `_SCENE_RESPONSE`/`_STATE_RESPONSE`/`_PROGRESS_RESPONSE` to match post-Plan-A schema |
| `ccya/tests/test_prompt_audit.py` | modify | Phase 02: drop `last_turn_failed` kwarg from byte-stability test |
| `ccya/tests/test_names.py` | modify | Phase 02: drop `last_turn_failed: []` key from narrate ctx fixture |
| `ccya/tests/test_engine_pipeline.py` | modify | Phase 04: drop `"failed": []` from `_state_response()` helper |
| `ccya/docs/ARCHITECTURE.md` | modify | Phase 06: rewrite Step 2a/2b/2c diagrams, Delta Merge node, and Cross-Pipeline arrows for post-Plan-A field routing; drop `last_turn_failed` (N7) input |
| `ccya/docs/REPOMAP/state.md` | modify | Phase 06: change "from progress extractor" → "from scene extractor" for `pending_gm_beat` |
| `ccya/docs/REPOMAP/engine.md` | modify | Phase 06: shrink `_run_extraction_pipeline` return tuple from 7 → 6, drop `last_turn_failed` from `_narrate_messages` signature |
| `ccya/docs/plans/eval-results-remediation/A-eval-results-remediation-pipeline-field-routing.md` | modify | Phase 06: replace `docs/REPOMAP/extraction.md` pointer with `docs/REPOMAP/engine.md` |
| `ccya/docs/plans/eval-results-remediation/B-eval-results-remediation-pressure-rules.md` | modify | Phase 06: same pointer fix |
| `ccya/docs/plans/eval-results-remediation/C-eval-results-remediation-gm-beat-enforcement.md` | modify | Phase 06: same pointer fix |
| `ccya/docs/plans/eval-results-remediation/D-eval-results-remediation-quest-state-extraction.md` | modify | Phase 06: same pointer fix |
| `ccya/docs/plans/TODO.md` | modify | Add `four-plans-cleanup` entry under P3, and mark Plans A/B/C/D `[x]` complete |

## Firm decisions
1. **No prompt-token ceilings.** Per project owner: prompts will be tuned by hand. Tests are commented out (not deleted) so they document past intent and can be revisited if needed; no replacement assertion.
2. **`failed` is gone permanently.** Plan A removed the LLM output; this cleanup removes the engine plumbing, the narrator template block, and all tests. We do not preserve a hook "for future use." If someone wants narrator failure feedback later, they will design it explicitly.
3. **`gm_beat` lives in `state.meta.pending_gm_beat`** (engine code) and is sourced from the **scene** extractor (not progress). All comments and docs use this language.
4. **Eval engine is out of scope.** Anything under `ccya/ccya/eval/`, `evals/`, the universal-asserts file, eval scenarios, eval rubrics, or stored eval runs is left untouched even when known wrong (e.g. `state.scene.pending_gm_beat` path mismatch, `KNOWN_ASSERT_FIELDS` stale, `gm_beat_lifecycle.py` asserts wrong path). These are explicitly tracked in this plan's "Out of scope" section so the next plan can sweep them.
5. **REPOMAP doc for engine internals is `docs/REPOMAP/engine.md`.** There is no `docs/REPOMAP/extraction.md` and there will not be one — the extraction pipeline is documented inside `engine.md`.
6. **Phase ordering is strict.** Phases 01–04 modify code. Phases 05–06 are doc-only and depend on the prior code phases having landed (because they cite line numbers and signatures). The executor must run phases in numeric order.
7. **Validation gate.** Every code-touching phase ends with `make check && make test`. Doc-only phases (05 if option b, 06) end with `make check` only.

## Conflicts and overlap
None. No other open plan in `docs/plans/` modifies any of the listed files. Plans A–D are completed-but-not-yet-archived; this plan finishes that archival in Phase 06's TODO.md update.

---

## Implementation — Phase 01: Remove token-budget tests

### Context files to load
- `ccya/tests/test_engine_pipeline.py`
- `ccya/AGENTS.md` (to confirm no commented-out-code rule applies; it does, but the user has explicitly authorized this exception — record that in the comment).

### Overview
Comment out (do not delete) the `PROMPT_CEILINGS_CHARS` dict and the `TestTokenBudgetCeilings` class in `tests/test_engine_pipeline.py`. Add a single explanatory note above the block citing the project owner decision so future readers know why AGENTS.md "no commented-out code" was waived here.

### Detailed steps

#### Step 01.1 — Comment out the ceilings dict and class

**File:** `ccya/tests/test_engine_pipeline.py`

**What:** Replace lines 187–292 (the `# Class A: Token-budget ceilings` banner block plus `PROMPT_CEILINGS_CHARS` dict plus the entire `TestTokenBudgetCeilings` class) with the block below. The lines after this block (`# Class B: Multi-turn invariants` and onward) remain untouched.

**Why:** Project owner explicitly removed all hard and soft prompt-size ceilings. The tests are kept commented (not deleted) so the historical intent and the per-stream limits we used to enforce are still discoverable by anyone investigating prompt growth.

**Code Snippet**
```python
# ---------------------------------------------------------------------------
# Class A: Token-budget ceilings — DISABLED
# ---------------------------------------------------------------------------
#
# These tests enforced per-stream character ceilings on rendered prompts.
# They are intentionally commented out (rather than deleted) per project
# owner direction: prompts are now allowed to grow as needed and will be
# trimmed by hand. AGENTS.md "no commented-out code" rule is waived for
# this single block because the historical ceilings document past intent
# and may be revisited.
#
# PROMPT_CEILINGS_CHARS = {
#     "rules.system": 6_000,
#     "rules.user": 8_000,
#     "narrate.system": 8_000,
#     "narrate.user": 18_000,
#     "scene.system": 10_000,
#     "scene.user": 14_000,
#     "state.system": 8_000,
#     "state.user": 14_000,
#     "progress.system": 9_000,
#     "progress.user": 14_000,
# }
#
#
# class TestTokenBudgetCeilings:
#     """DISABLED — see banner above."""
#     pass
```

**Validation:** `uv run pytest tests/test_engine_pipeline.py -q` — must pass with no `TestTokenBudgetCeilings` items collected. The remaining classes (`Class B: Multi-turn invariants`, `Class C: Rules + scope correctness`, `Class D: Quest and state extraction fixes`) must still run.

### Tests to write or update
None beyond the comment-out described above. The replaced tests stay disabled.

### REPOMAP updates required
None. `docs/REPOMAP/testing.md` line 7 says `test_engine_pipeline.py — Token-budget ceilings, multi-turn invariants, scope-gating tests`; that line will be updated in Phase 06 step 06.5 (single doc-edit phase).

### Risks
1. CI relied on these tests catching prompt bloat. **Mitigation:** owner is aware and explicitly chose to remove the ceilings.
2. A future contributor sees the commented block and uncomments it without context. **Mitigation:** the banner explains why and references project-owner direction.

---

## Implementation — Phase 02: Remove dead `failed` plumbing

### Context files to load
- `ccya/ccya/engine/turn.py` (lines 280–605 for `run_turn`, lines 857–1265 for `run_turn_retry`)
- `ccya/ccya/engine/extraction.py` (lines 365–600 for `_run_extraction_pipeline`)
- `ccya/ccya/engine/narrate.py` (full file, 160 lines)
- `ccya/ccya/prompts/narrate_user.j2` (lines 95–115)
- `ccya/tests/test_engine_smoke.py` (lines 510–595 for `last_turn_failed` tests)
- `ccya/tests/test_prompt_audit.py` (lines 80–105)
- `ccya/tests/test_names.py` (lines 155–180)
- `ccya/AGENTS.md` (dead-code-removal policy)

### Overview
Plan A removed the `failed` field from `StateExtractResult` and from the LLM-extractor schema. The engine still threads a permanently-empty `failed: list[str]` through both `run_turn` and `run_turn_retry`, the `_run_extraction_pipeline` return tuple still has a `failed` slot at index 3, the narrator still receives `last_turn_failed=last_events[0].get("failed", [])` (which is always `[]`), and `narrate_user.j2` still renders a `## last_turn_failed` block (which is now permanently dead). Three tests still exercise the `last_turn_failed` parameter. This phase removes the entire chain.

### Detailed steps

#### Step 02.1 — Shrink `_run_extraction_pipeline` return tuple

**File:** `ccya/ccya/engine/extraction.py`

**What:** Modify the function signature, docstring, and `return` block to drop the `failed` slot at index 3. The return becomes a 6-tuple.

**Why:** The slot is always `[]` (line 594 of the current file). It exists only because Plan A explicitly preserved the position for backwards compatibility. AGENTS.md forbids "no backwards compatibility required" and dead slots.

**Code Snippet** (replace the function signature line, the docstring line, and the return block):

Locate the current signature (lines 365–379):
```python
async def _run_extraction_pipeline(
    env: "Environment",
    state: dict[str, Any],
    narration: str,
    *,
    active_domains: list[str],
    rules_outcome: "RulesOutcome | None" = None,
    intent: "IntentEnvelope | None" = None,
    config: "EngineConfig",
    trace_id: str,
    turn_no: int,
    deescalate: bool = False,
    quest_ages: list[dict[str, Any]] | None = None,
    recent_turns: list[dict[str, Any]] | None = None,
) -> tuple["StateDelta", list[str], str, list[str], dict[str, Any], "ProgressExtractResult", "SceneExtractResult"]:
    """Run the three extraction streams in sequence.

    Returns: (merged_delta, actions, outcome_summary, failed, per_stream_event_data, progress_result, scene_result)
    """
```

Replace with:
```python
async def _run_extraction_pipeline(
    env: "Environment",
    state: dict[str, Any],
    narration: str,
    *,
    active_domains: list[str],
    rules_outcome: "RulesOutcome | None" = None,
    intent: "IntentEnvelope | None" = None,
    config: "EngineConfig",
    trace_id: str,
    turn_no: int,
    deescalate: bool = False,
    quest_ages: list[dict[str, Any]] | None = None,
    recent_turns: list[dict[str, Any]] | None = None,
) -> tuple["StateDelta", list[str], str, dict[str, Any], "ProgressExtractResult", "SceneExtractResult"]:
    """Run the three extraction streams in sequence.

    Returns: (merged_delta, actions, outcome_summary, per_stream_event_data, progress_result, scene_result)
    """
```

Locate the current return (lines 590–598):
```python
    return (
        merged,
        progress_result.actions,
        progress_result.outcome_summary,
        [],
        extraction_event,
        progress_result,
        scene_result,
    )
```

Replace with:
```python
    return (
        merged,
        progress_result.actions,
        progress_result.outcome_summary,
        extraction_event,
        progress_result,
        scene_result,
    )
```

**Validation:** `uv run python -c "import ast, pathlib; ast.parse(pathlib.Path('ccya/engine/extraction.py').read_text())"` — file still parses. `grep -n "failed" ccya/ccya/engine/extraction.py` returns no matches.

#### Step 02.2 — Update `run_turn` unpacking and event dict

**File:** `ccya/ccya/engine/turn.py`

**What:** Three edits inside the `run_turn` function:

(a) Remove the `last_turn_failed` block (lines 296–300). Locate:
```python
        # Load failed preconditions from the most recent event (for narrate feedback)
        last_events = load_recent_events(save_dir, 1)
        last_turn_failed: list[str] = []
        if last_events:
            last_turn_failed = last_events[0].get("failed", [])
```
Delete those five lines outright.

(b) Remove the `last_turn_failed=last_turn_failed,` kwarg from the `_narrate_messages(...)` call. Locate the line (currently line 444):
```python
            last_turn_failed=last_turn_failed,
```
Delete it.

(c) Update the comment on line 417 that says "previous turn's progress extraction" — change `progress` to `scene`. Locate:
```python
        # Read pending_gm_beat from previous turn's progress extraction
        _pending_gm_beat = (state.get("meta") or {}).get("pending_gm_beat")
```
Replace the comment line with:
```python
        # Read pending_gm_beat from previous turn's scene extraction
        _pending_gm_beat = (state.get("meta") or {}).get("pending_gm_beat")
```

(d) Update the extraction-pipeline unpacking and drop the `failed` plumbing (lines 531–561). Locate:
```python
        delta = None
        actions = []
        outcome_summary: str = ""
        failed: list[str] = []
        extraction_event: dict[str, Any] = {}

        try:
            delta, actions, outcome_summary, failed, extraction_event, progress_result, scene_result = (
                await _run_extraction_pipeline(
                    env, state, narrative,
                    active_domains=_active_domains,
                    rules_outcome=outcome,
                    intent=intent,
                    config=config,
                    trace_id=trace_id,
                    turn_no=turn_no,
                    deescalate=deescalate,
                    quest_ages=quest_ages,
                    recent_turns=recent_turns,
                )
            )
            # Store gm_beat for next turn's narration
            if scene_result and scene_result.gm_beat and scene_result.gm_beat.type:
                state.setdefault("meta", {})["pending_gm_beat"] = scene_result.gm_beat.model_dump(exclude_none=True)
            if failed:
                _log.info(
                    "Turn %d: failed preconditions: %s",
                    turn_no,
                    failed,
                    extra={"trace_id": trace_id},
                )
        except Exception as exc:
            errors.append({"trace_id": trace_id, "message": str(exc)})
```

Replace with:
```python
        delta = None
        actions = []
        outcome_summary: str = ""
        extraction_event: dict[str, Any] = {}

        try:
            delta, actions, outcome_summary, extraction_event, progress_result, scene_result = (
                await _run_extraction_pipeline(
                    env, state, narrative,
                    active_domains=_active_domains,
                    rules_outcome=outcome,
                    intent=intent,
                    config=config,
                    trace_id=trace_id,
                    turn_no=turn_no,
                    deescalate=deescalate,
                    quest_ages=quest_ages,
                    recent_turns=recent_turns,
                )
            )
            # Store gm_beat for next turn's narration
            if scene_result and scene_result.gm_beat and scene_result.gm_beat.type:
                state.setdefault("meta", {})["pending_gm_beat"] = scene_result.gm_beat.model_dump(exclude_none=True)
        except Exception as exc:
            errors.append({"trace_id": trace_id, "message": str(exc)})
```

(e) Drop the `failed` event-dict key (line 736). Locate:
```python
            "changes": changes,
            "failed": failed if failed else [],
            # Prompt logging (for turn viewer)
```
Replace with:
```python
            "changes": changes,
            # Prompt logging (for turn viewer)
```

**Why:** With the LLM never producing `failed`, the read-from-prior-event always gets `[]`, the local variable is always `[]`, the log block never fires, the narrator template block never renders, and the event field is always `[]`. Per AGENTS.md "Remove dead code immediately."

**Validation:** `grep -n "failed" ccya/ccya/engine/turn.py` should return only references to `delta validation failed` (string content in error messages, currently lines 633 and 1146). No `last_turn_failed` matches. No `failed: list[str]` matches. No `"failed":` event-dict matches.

#### Step 02.3 — Update `run_turn_retry` (mirror of step 02.2)

**File:** `ccya/ccya/engine/turn.py`

**What:** Apply the same five edits to `run_turn_retry`. Locations:

(a) Lines 912–915:
```python
        last_events = load_recent_events(save_dir, 1)
        last_turn_failed: list[str] = []
        if last_events:
            last_turn_failed = last_events[0].get("failed", [])
```
Delete these four lines.

(b) Line 958:
```python
            last_turn_failed=last_turn_failed,
```
Delete.

(c) `run_turn_retry` does not have a comment matching `previous turn's progress extraction` — skip step (c) here.

(d) Lines 1049–1080:
```python
        delta = None
        actions = []
        outcome_summary: str = ""
        failed: list[str] = []
        extraction_event: dict[str, Any] = {}

        try:
            delta, actions, outcome_summary, failed, extraction_event, progress_result, scene_result = (
                await _run_extraction_pipeline(
                    env, state, narrative,
                    active_domains=_active_domains,
                    rules_outcome=outcome,
                    intent=intent,
                    config=config,
                    trace_id=trace_id,
                    turn_no=turn_no,
                    deescalate=False,
                    quest_ages=[],
                    recent_turns=recent_turns,
                )
            )
            if scene_result and scene_result.gm_beat and scene_result.gm_beat.type:
                state.setdefault("meta", {})["pending_gm_beat"] = scene_result.gm_beat.model_dump(exclude_none=True)
            if failed:
                _log.info(
                    "Turn %d: failed preconditions: %s",
                    turn_no,
                    failed,
                    extra={"trace_id": trace_id},
                )
        except Exception as exc:
            errors.append({"trace_id": trace_id, "message": str(exc)})
```

Replace with:
```python
        delta = None
        actions = []
        outcome_summary: str = ""
        extraction_event: dict[str, Any] = {}

        try:
            delta, actions, outcome_summary, extraction_event, progress_result, scene_result = (
                await _run_extraction_pipeline(
                    env, state, narrative,
                    active_domains=_active_domains,
                    rules_outcome=outcome,
                    intent=intent,
                    config=config,
                    trace_id=trace_id,
                    turn_no=turn_no,
                    deescalate=False,
                    quest_ages=[],
                    recent_turns=recent_turns,
                )
            )
            if scene_result and scene_result.gm_beat and scene_result.gm_beat.type:
                state.setdefault("meta", {})["pending_gm_beat"] = scene_result.gm_beat.model_dump(exclude_none=True)
        except Exception as exc:
            errors.append({"trace_id": trace_id, "message": str(exc)})
```

(e) Line 1245:
```python
            "changes": changes,
            "failed": failed if failed else [],
            "rules_prompt": {
```
Replace with:
```python
            "changes": changes,
            "rules_prompt": {
```

**Validation:** Same as 02.2.

#### Step 02.4 — Drop `last_turn_failed` from `narrate.py`

**File:** `ccya/ccya/engine/narrate.py`

**What:** Remove the parameter and the corresponding context-dict entry.

**Code Snippet** (replace the full `_narrate_messages` signature block and `user_ctx` dict):

Locate (lines 12–56):
```python
def _narrate_messages(
    env: Any,
    state: dict[str, Any],
    user_input: str,
    *,
    chronicle_tail: str = "",
    recent_turns: list[dict[str, Any]] = [],
    enable_narrate_thinking: bool = False,
    pack_style: str = "",
    narrator_rules: list[str] = [],
    rules_outcome: "RulesOutcome | None" = None,
    npc_name_pool: dict[str, list[str]] = {},
    last_turn_failed: list[str] = [],
    recently_left: list[dict[str, Any]] = [],
    momentum: int = 0,
    pending_gm_beat: dict[str, Any] | None = None,
    deescalate: bool = False,
    ages: dict[str, int] | None = None,
    known_npcs: list[dict[str, Any]] = [],
    present_npcs: list[dict[str, Any]] = [],
    world_factions: list[dict[str, str]] = [],
    world_locations: list[dict[str, str]] = [],
    pc_allegiance: str | None = None,
) -> list[dict[str, str]]:
    user_ctx = {
        "state": state,
        "chronicle_tail": chronicle_tail,
        "recent_turns": recent_turns,
        "rules_outcome": rules_outcome,
        "npc_name_pool": npc_name_pool,
        "last_turn_failed": last_turn_failed,
        "recently_left": recently_left,
        "user_input": user_input,
        "momentum": momentum,
        "pending_gm_beat": pending_gm_beat,
        "meta": state.get("meta", {}),
        "scene": state.get("scene", {}),
        "deescalate": deescalate,
        "ages": ages or {},
        "known_npcs": known_npcs,
        "present_npcs": present_npcs,
        "world_factions": world_factions,
        "world_locations": world_locations,
        "pc_allegiance": pc_allegiance,
    }
```

Replace with:
```python
def _narrate_messages(
    env: Any,
    state: dict[str, Any],
    user_input: str,
    *,
    chronicle_tail: str = "",
    recent_turns: list[dict[str, Any]] = [],
    enable_narrate_thinking: bool = False,
    pack_style: str = "",
    narrator_rules: list[str] = [],
    rules_outcome: "RulesOutcome | None" = None,
    npc_name_pool: dict[str, list[str]] = {},
    recently_left: list[dict[str, Any]] = [],
    momentum: int = 0,
    pending_gm_beat: dict[str, Any] | None = None,
    deescalate: bool = False,
    ages: dict[str, int] | None = None,
    known_npcs: list[dict[str, Any]] = [],
    present_npcs: list[dict[str, Any]] = [],
    world_factions: list[dict[str, str]] = [],
    world_locations: list[dict[str, str]] = [],
    pc_allegiance: str | None = None,
) -> list[dict[str, str]]:
    user_ctx = {
        "state": state,
        "chronicle_tail": chronicle_tail,
        "recent_turns": recent_turns,
        "rules_outcome": rules_outcome,
        "npc_name_pool": npc_name_pool,
        "recently_left": recently_left,
        "user_input": user_input,
        "momentum": momentum,
        "pending_gm_beat": pending_gm_beat,
        "meta": state.get("meta", {}),
        "scene": state.get("scene", {}),
        "deescalate": deescalate,
        "ages": ages or {},
        "known_npcs": known_npcs,
        "present_npcs": present_npcs,
        "world_factions": world_factions,
        "world_locations": world_locations,
        "pc_allegiance": pc_allegiance,
    }
```

**Validation:** `grep -n "last_turn_failed" ccya/ccya/engine/narrate.py` — no matches.

#### Step 02.5 — Drop the `## last_turn_failed` block from `narrate_user.j2`

**File:** `ccya/ccya/prompts/narrate_user.j2`

**What:** Delete lines 101–105 (the entire `{% if last_turn_failed -%} ... {% endif -%}` block):
```jinja
{% if last_turn_failed -%}
## last_turn_failed (already resolved by prior narrator; do NOT retry)
{% for f in last_turn_failed %}- {{ f }}
{% endfor %}
{% endif -%}
```
After deletion, the surrounding context becomes:
```jinja
{% endif -%}
{% if known_npcs -%}
```
(line that was 100, then jumps to what is now line 101 which used to be line 106).

**Validation:** `grep -n "last_turn_failed" ccya/ccya/prompts/narrate_user.j2` — no matches. Render the template once with `last_turn_failed` undefined to confirm Jinja does not raise.

#### Step 02.6 — Remove `last_turn_failed` test cases and kwargs

**File:** `ccya/tests/test_engine_smoke.py`

**What:** Two edits:

(a) Delete `test_narrate_last_turn_failed` (lines 524–533) and `test_narrate_no_last_turn_failed_when_empty` (lines 535–540) outright.

(b) In `test_narrate_system_byte_stable_across_turns` (lines 578–594), delete the `last_turn_failed=["did not succeed"],` kwarg from the `_narrate_messages(...)` call (line 590).

**Why:** The parameter no longer exists (step 02.4); these tests would fail import or fail kwarg validation.

**Validation:** `uv run pytest tests/test_engine_smoke.py -q -k narrate` — must pass with the two deleted tests no longer collected.

#### Step 02.7 — Drop `last_turn_failed` from `test_prompt_audit.py`

**File:** `ccya/tests/test_prompt_audit.py`

**What:** Delete the `last_turn_failed=["did not succeed"],` kwarg from the `_narrate_messages(...)` call inside `test_narrate_system_byte_stable` (line 95). Surrounding code is unchanged.

**Validation:** `uv run pytest tests/test_prompt_audit.py -q` — must pass.

#### Step 02.8 — Drop `last_turn_failed` from `test_names.py`

**File:** `ccya/tests/test_names.py`

**What:** In the inline `ctx` dict around line 158, delete the line:
```python
            "last_turn_failed": [],
```

**Why:** The Jinja template no longer references this variable; the test ctx need not provide it. Removing keeps fixtures honest.

**Validation:** `uv run pytest tests/test_names.py -q` — must pass.

### Tests to write or update
All test edits are described above. No new tests added. The deletion of the two `test_narrate_last_turn_failed*` tests is intentional: with the parameter and template block gone, the behavior they covered no longer exists and there is nothing left to assert.

### REPOMAP updates required
`docs/REPOMAP/engine.md` line 70 lists `last_turn_failed=None,` in the `_narrate_messages` signature. Phase 06 step 06.4 removes it; do NOT update in this phase.

### Risks
1. Some other module (server route, debug panel) may read `event["failed"]`. **Mitigation:** `grep -rn '"failed"' ccya/ccya/server/ ccya/ccya/state/` returns nothing. Confirmed clean before phase end.
2. The `last_turn_failed` block deletion drifts `narrate_user.j2` by 5 lines; any downstream test that pins line numbers breaks. **Mitigation:** no such test exists (`grep -rn 'narrate_user.j2:[0-9]' ccya/tests/` is empty).
3. A future feature genuinely needs narrator failure feedback. **Mitigation:** they design it explicitly; no compatibility scaffolding preserved here per AGENTS.md.

---

## Implementation — Phase 03: Prompt + extraction cleanup

### Context files to load
- `ccya/ccya/prompts/extract_progress_user.j2` (full, 72 lines)
- `ccya/ccya/prompts/extract_scene_user.j2` (full, 60 lines)
- `ccya/ccya/engine/extraction.py` (lines 365–415 around the scene extractor call)

### Overview
Two narrow cleanups:
1. `extract_progress_user.j2` has a dead `{% for qa in quest_ages %}` block (lines 32–36); `quest_ages` is no longer passed to the progress extractor (Plan A moved it to scene). The block silently iterates over `Undefined` and emits nothing.
2. `_run_extraction_pipeline` passes `(recent_turns or [])[-2:]` to the scene extractor, but `extract_scene_user.j2` only references `recent_turns[-1]`. The T-2 element is rendered into nothing. Trim the slice to `[-1:]` for the scene call.

### Detailed steps

#### Step 03.1 — Drop dead `quest_ages` block from progress user template

**File:** `ccya/ccya/prompts/extract_progress_user.j2`

**What:** Delete lines 32–36:
```jinja
{% for qa in quest_ages %}
{% if qa.stalled_turns >= 3%}
⚠ Quest "{{ qa.title }}" stalled for {{ qa.stalled_turns }} turns. Advance it, branch it, or mark an objective failed.
{% endif %}
{% endfor %}
```
After deletion, the surrounding context becomes (line 31 followed by what was line 37):
```jinja
{% endif -%}
{% endif -%}

{% if "recent_events" in active_domains -%}
```

**Why:** `extract.progress` no longer receives `quest_ages` — that signal moved to `extract.scene` per Plan A. The undefined variable iteration is a silent no-op today; removing it makes the template's actual contract explicit.

**Validation:** `grep -n "quest_ages" ccya/ccya/prompts/extract_progress_user.j2` — no matches. `grep -n "quest_ages" ccya/ccya/prompts/extract_scene_user.j2` — should still match (scene template legitimately uses it).

#### Step 03.2 — Trim `recent_turns` slice for the scene call

**File:** `ccya/ccya/engine/extraction.py`

**What:** In `_run_extraction_pipeline`, the scene-extractor call (around line 413) currently passes:
```python
            recent_turns=(recent_turns or [])[-2:],
```
Change to:
```python
            recent_turns=(recent_turns or [])[-1:],
```

The progress-extractor call (around line 507) keeps `[-2:]` because `extract_progress_user.j2` does use `recent_turns[-2]` for the T-2 prior-turn-narration block.

**Why:** The scene template only references `recent_turns[-1]` (`extract_scene_user.j2` lines 51–56). Passing two turns wastes context space.

**Validation:** Diff `extract_scene_user.j2` for `recent_turns[`: only `recent_turns[-1]` should appear. `extract_progress_user.j2` should still reference `recent_turns[-2]`.

### Tests to write or update
No test changes required. Existing scope-gating tests in `test_engine_pipeline.py` will exercise the new slice.

### REPOMAP updates required
None for this phase. Phase 06 carries the broader doc sweep.

### Risks
1. Some test that builds a fixture with two recent turns now sees only one passed to scene. **Mitigation:** no test explicitly verifies the T-2 reaches the scene template; `grep -rn 'recent_turns\[-2\]' ccya/tests/` returns no matches.

---

## Implementation — Phase 04: Test fixture cleanup

### Context files to load
- `ccya/tests/test_engine_smoke.py` (lines 140–170 for `_SCENE/_STATE/_PROGRESS_RESPONSE` constants)
- `ccya/tests/test_engine_pipeline.py` (lines 300–360 for the `_state_response`/`_progress_response`/`_scene_response` helper functions)
- `ccya/ccya/models.py` (Pydantic schemas to confirm shape)

### Overview
The `_FakeLLM` per-stream JSON fixtures still emit fields that Plan A re-routed or removed. Pydantic v2's default `extra: ignore` silently drops them, so tests pass — but the fixtures lie about the schema. Update them to match the post-Plan-A `SceneExtractResult`, `StateExtractResult`, and `ProgressExtractResult` shape.

### Detailed steps

#### Step 04.1 — Rewrite `_SCENE_RESPONSE`

**File:** `ccya/tests/test_engine_smoke.py`

**What:** Replace lines 143–150:
```python
_SCENE_RESPONSE = json.dumps({
    "scene_tags": ["exploration"],
    "scene_tagline": "Quiet corridor stretches ahead",
    "location_change": None,
    "location_description": None,
    "actions": ["Look around carefully", "Check the panels", "Listen at the door", "Go back"],
    "outcome_summary": "You step through the airlock into silence.",
})
```
With:
```python
_SCENE_RESPONSE = json.dumps({
    "scene_tags": ["exploration"],
    "scene_tagline": "Quiet corridor stretches ahead",
    "location_change": None,
    "location_description": None,
    "npc_add": [],
    "npc_remove": [],
    "npc_update": [],
    "compendium_npc_update": [],
    "scene_pressure_add": [],
    "scene_pressure_remove": [],
    "scene_pressure_update": [],
    "gm_beat": None,
})
```

**Why:** Plan A moved `actions` and `outcome_summary` to progress; scene now owns `npc_*`, `compendium_npc_update`, `scene_pressure_*`, and `gm_beat`. Mirror the live schema.

**Validation:** `uv run pytest tests/test_engine_smoke.py -q` — must pass; no test should break since `extra: ignore` was hiding the drift.

#### Step 04.2 — Rewrite `_STATE_RESPONSE`

**File:** `ccya/tests/test_engine_smoke.py`

**What:** Replace lines 152–159:
```python
_STATE_RESPONSE = json.dumps({
    "inventory_add": [],
    "inventory_remove": [],
    "inventory_update": [],
    "pc_condition_add": [],
    "pc_condition_remove": [],
    "failed": [],
})
```
With:
```python
_STATE_RESPONSE = json.dumps({
    "inventory_add": [],
    "inventory_remove": [],
    "inventory_update": [],
    "pc_condition_add": [],
    "pc_condition_remove": [],
})
```

**Why:** Plan A removed `failed` from `StateExtractResult`.

**Validation:** Same as 04.1.

#### Step 04.3 — Rewrite `_PROGRESS_RESPONSE`

**File:** `ccya/tests/test_engine_smoke.py`

**What:** Replace lines 161–167:
```python
_PROGRESS_RESPONSE = json.dumps({
    "quest_updates": [],
    "recent_events_add": [],
    "recent_events_update": [],
    "recent_events_remove": [],
    "compendium_npc_update": [],
})
```
With:
```python
_PROGRESS_RESPONSE = json.dumps({
    "quest_updates": [],
    "recent_events_add": [],
    "recent_events_update": [],
    "recent_events_remove": [],
    "actions": [],
    "outcome_summary": "",
})
```

**Why:** Plan A moved `compendium_npc_update` to scene; `actions` and `outcome_summary` moved into progress.

**Validation:** Same as 04.1.

#### Step 04.4 — Drop `"failed": []` from `_state_response()` helper

**File:** `ccya/tests/test_engine_pipeline.py`

**What:** In the `_state_response()` function (around lines 300–315), delete the `"failed": [],` key:

Locate:
```python
def _state_response(
    *,
    inv_add: list[dict] | None = None,
    inv_remove: list[dict] | None = None,
    cond_add: list[dict] | None = None,
) -> str:
    return json.dumps(
        {
            "inventory_add": inv_add or [],
            "inventory_remove": inv_remove or [],
            "inventory_update": [],
            "pc_condition_add": cond_add or [],
            "pc_condition_remove": [],
            "failed": [],
        },
    )
```
Replace with:
```python
def _state_response(
    *,
    inv_add: list[dict] | None = None,
    inv_remove: list[dict] | None = None,
    cond_add: list[dict] | None = None,
) -> str:
    return json.dumps(
        {
            "inventory_add": inv_add or [],
            "inventory_remove": inv_remove or [],
            "inventory_update": [],
            "pc_condition_add": cond_add or [],
            "pc_condition_remove": [],
        },
    )
```

**Validation:** `uv run pytest tests/test_engine_pipeline.py -q` — must pass.

### Tests to write or update
No new tests; only the four fixtures above are corrected.

### REPOMAP updates required
None.

### Risks
1. A retry test relied on `"failed"` propagating through. **Mitigation:** verified by `grep -rn 'failed' ccya/tests/` — only the references already enumerated; no asserts on `event["failed"]`.

---

## Implementation — Phase 05: Narration markers alignment

### Context files to load
- `ccya/docs/PROMPTING.md` (rule 5)
- `ccya/ccya/prompts/extract_scene_user.j2` (lines 58–60)
- `ccya/ccya/prompts/extract_state_user.j2` (lines 47–49)
- `ccya/ccya/prompts/extract_progress_user.j2` (lines 69–71 — note line numbers shift after Phase 03)
- `ccya/ccya/prompts/narrate_user.j2` (line 141, marker reference)
- `ccya/ccya/prompts/rules_user.j2` (line 14, marker reference)

### Overview
PROMPTING.md rule 5 mandates `=== NARRATION ===` / `=== END NARRATION ===` everywhere. Today, `narrate_user.j2` and `rules_user.j2` use `=== PLAYER INPUT ===` / `=== END PLAYER INPUT ===` (acceptable per rule 5), but the three extract templates use `## CURRENT TURN NARRATION` / `## END CURRENT TURN NARRATION` — which violates rule 5. This phase aligns the codebase one of two ways. **The executor must NOT proceed until the project owner picks option (a) or (b).**

### Ambiguities requiring resolution before execution
1. Pick one of:
   - **Option (a):** rewrite the three extract user templates to use `=== NARRATION ===` / `=== END NARRATION ===`. Aligns templates with PROMPTING.md rule 5.
   - **Option (b):** update PROMPTING.md rule 5 to record `## CURRENT TURN NARRATION` as the actual extract convention, and explain why narrate uses a different marker style. Aligns docs with templates.
   
   Recommendation: option (a) — single live convention is easier to enforce and matches the spirit of the rule. But (b) is acceptable if the owner prefers no live-prompt churn.

### Detailed steps (option a)

#### Step 05a.1 — Rename markers in `extract_scene_user.j2`

**File:** `ccya/ccya/prompts/extract_scene_user.j2`

**What:** Replace lines 58–60:
```jinja
## CURRENT TURN NARRATION
{{ narration }}
## END CURRENT TURN NARRATION
```
With:
```jinja
=== NARRATION ===
{{ narration }}
=== END NARRATION ===
```

#### Step 05a.2 — Rename markers in `extract_state_user.j2`

**File:** `ccya/ccya/prompts/extract_state_user.j2`

**What:** Replace lines 47–49:
```jinja
## CURRENT TURN NARRATION
{{ narration }}
## END CURRENT TURN NARRATION
```
With:
```jinja
=== NARRATION ===
{{ narration }}
=== END NARRATION ===
```

#### Step 05a.3 — Rename markers in `extract_progress_user.j2`

**File:** `ccya/ccya/prompts/extract_progress_user.j2`

**What:** Replace the last three lines (after Phase 03 deletion the line numbers shift; the relevant block reads):
```jinja
## CURRENT TURN NARRATION
{{ narration }}
## END CURRENT TURN NARRATION
```
With:
```jinja
=== NARRATION ===
{{ narration }}
=== END NARRATION ===
```

**Validation (option a, all three steps):** `grep -rn '## CURRENT TURN NARRATION' ccya/ccya/prompts/` — no matches. `grep -rn '=== NARRATION ===' ccya/ccya/prompts/` — exactly three matches, one per extract user template. `uv run pytest tests/test_engine_smoke.py tests/test_engine_pipeline.py tests/test_prompt_audit.py -q` — all green; the markers are not asserted on by name in tests.

### Detailed steps (option b)

#### Step 05b.1 — Update PROMPTING.md rule 5

**File:** `ccya/docs/PROMPTING.md`

**What:** Replace the body of rule 5 (lines 41–43):
```markdown
### 5. One delimiter pair for untrusted long content
Use `=== NARRATION ===` / `=== END NARRATION ===` and `=== PLAYER INPUT ===` / `=== END PLAYER INPUT ===` everywhere. No `## CURRENT TURN NARRATION`, no bare unwrapped narration, no inconsistent `## Player's current input`.
```
With:
```markdown
### 5. One delimiter pair per role
Two delimiter conventions, applied consistently:
- **`=== PLAYER INPUT ===` / `=== END PLAYER INPUT ===`** — the player's raw turn input. Used by `rules_user.j2` and `narrate_user.j2`.
- **`## CURRENT TURN NARRATION` / `## END CURRENT TURN NARRATION`** — the narrator's prose handed to the three extractors. Used by `extract_scene_user.j2`, `extract_state_user.j2`, `extract_progress_user.j2`.

The two markers signal different trust models: `=== PLAYER INPUT ===` marks user-controlled untrusted text; `## CURRENT TURN NARRATION` marks engine-controlled narration prose with a stable header that reads naturally inside markdown-style extract prompts. Do not invent a third convention.
```

**Validation (option b):** No code changes. Rule 5 now matches reality; rule 8 ("One home per directive") is unaffected.

### Tests to write or update
None.

### REPOMAP updates required
None.

### Risks
1. Option (a) is a live-prompt change; the model may parse slightly differently. **Mitigation:** the three extract prompts use the marker only as a section boundary; no rule references the literal marker text. Smoke tests cover round-trip extraction.
2. Option (b) freezes drift. **Mitigation:** explicit by design — owner decision.

---

## Implementation — Phase 06: ARCHITECTURE.md, REPOMAP, plan-doc pointer fixes, TODO.md

### Context files to load
- `ccya/docs/ARCHITECTURE.md` (full, 504 lines)
- `ccya/docs/REPOMAP/state.md` (line 45 area)
- `ccya/docs/REPOMAP/engine.md` (lines 70 and 91 area)
- `ccya/docs/REPOMAP/testing.md` (line 7)
- `ccya/docs/plans/eval-results-remediation/A-eval-results-remediation-pipeline-field-routing.md`
- `ccya/docs/plans/eval-results-remediation/B-eval-results-remediation-pressure-rules.md`
- `ccya/docs/plans/eval-results-remediation/C-eval-results-remediation-gm-beat-enforcement.md`
- `ccya/docs/plans/eval-results-remediation/D-eval-results-remediation-quest-state-extraction.md`
- `ccya/docs/plans/TODO.md`

### Overview
Pure documentation pass that aligns the architecture diagrams, REPOMAP entries, plan-doc cross-references, and TODO.md to the post-Plan-A/B/C/D + post-Phase-02 reality. No code changes.

### Detailed steps

#### Step 06.1 — Fix Step 2a (Scene Extract) in ARCHITECTURE.md

**File:** `ccya/docs/ARCHITECTURE.md`

**What:** Replace the entire Step 2a `Inputs` and `Outputs` blocks (the mermaid `subgraph IN` and `subgraph OUT` for Step 2a, currently lines 180–204) with the schema-correct version below. Surrounding text (the introduction sentence, the `## Step 2a — Scene Extract` heading, the closing `> Note:` and `> Skippable:` blocks) is preserved.

Current `Inputs` block (lines 180–190):
```mermaid
    subgraph IN["Inputs"]
        S1["narrative (from Step 1)"]:::xstream
        S2["state.pc (name, tagline, bio, stats)"]
        S3["state.location"]
        S4["state.scene.present_npcs"]
        S5["state.pc.conditions"]
        S6["known_characters<br>(compact: id+name, up to 10 LRU<br>from compendium)"]
        S7["rules_outcome"]:::xstream
        S8["active_domains<br>(from Step 1 tail)"]:::xstream
        S9["known_locations<br>(currently always [] in engine — stub)"]
    end
```
Replace with:
```mermaid
    subgraph IN["Inputs"]
        S1["narrative (from Step 1)"]:::xstream
        S2["state.pc (name, tagline, bio, stats)"]
        S3["state.location"]
        S4["state.scene.present_npcs"]
        S5["state.pc.conditions"]
        S6["known_characters<br>(full roster: id, name, tags, notes<br>up to 10 LRU from compendium)"]
        S7["rules_outcome"]:::xstream
        S8["active_domains<br>(from Step 1 tail)"]:::xstream
        S9["scene_pressure (active threats)"]
        S10["deescalate flag<br>(success on active pressure)"]:::xstream
        S11["quest_ages<br>(stalled-quest signal)"]
        S12["recent_turns[-1:]<br>(T-1 prior narration)"]
    end
```

Current `Outputs` block (lines 196–204):
```mermaid
    subgraph OUT["Outputs — SceneExtractResult"]
        O1["scene_tags: list[str]"]:::outNode
        O2["scene_tagline: str (3–6 words for UI header)"]:::outNode
        O3["location_change: LocationRef | None<br>  id, name, description"]:::outNode
        O4["location_description: str | None"]:::outNode
        O5["present_npcs: list[NpcRef]<br>  id, name, title, notes, bio"]:::outNode
        O6["actions: list[str] (suggested next actions)"]:::outNode
        O7["outcome_summary: str"]:::outNode
    end
```
Replace with:
```mermaid
    subgraph OUT["Outputs — SceneExtractResult"]
        O1["scene_tags: list[str]"]:::outNode
        O2["scene_tagline: str (3–6 words for UI header)"]:::outNode
        O3["location_change: LocationRef | None<br>  id, name, description"]:::outNode
        O4["location_description: str | None"]:::outNode
        O5["npc_add / npc_remove / npc_update<br>  delta-form NPC presence changes"]:::outNode
        O6["compendium_npc_update<br>  durable identity changes"]:::outNode
        O7["scene_pressure_add / remove / update<br>  active-threat lifecycle"]:::outNode
        O8["gm_beat: GMBeat | None<br>  forward-facing storytelling beat"]:::outNode
    end
```

Then delete the now-stale `> **Note:** \`known_locations\` is passed to the template ...` paragraph (lines 210–212). Replace it with nothing — the surrounding `> **Skippable:**` and `> **Key forward dependency:**` blocks stay.

**Why:** Plan A moved `actions` and `outcome_summary` to progress; scene now owns `npc_*`, `compendium_npc_update`, `scene_pressure_*`, `gm_beat`. The `known_locations` stub line predates current code and was never accurate post-refactor.

**Validation:** `grep -n "known_locations" ccya/docs/ARCHITECTURE.md` — no matches. `grep -n "actions: list\[str\] (suggested" ccya/docs/ARCHITECTURE.md` — no matches inside Step 2a.

#### Step 06.2 — Fix Step 2b (State Extract) in ARCHITECTURE.md

**File:** `ccya/docs/ARCHITECTURE.md`

**What:** In the Step 2b `Outputs` block (currently lines 247–254), delete output node `O6`:
```mermaid
        O6["failed: list[str]<br>  (unmet preconditions this turn)"]:::outNode
```
The remaining nodes O1–O5 are correct.

**Validation:** Inside the Step 2b `subgraph OUT` block, `O6` should not appear.

#### Step 06.3 — Fix Step 2c (Progress Extract) in ARCHITECTURE.md

**File:** `ccya/docs/ARCHITECTURE.md`

**What:** Replace the entire Step 2c `Inputs` and `Outputs` blocks (currently lines 280–303) with:

Current `Inputs` block (lines 280–291):
```mermaid
    subgraph IN["Inputs"]
        S1["narrative (from Step 1)"]:::xstream
        S2["state.pc (name, bio, stats)"]
        S3["state.scene.recent_events"]
        S4["state.scene.world_state"]
        S5["active_quests (status=active only)"]
        S6["known_characters<br>(full: id, name, title, bio_preview,<br>up to 10 LRU from compendium)"]
        S7["rules_outcome"]:::xstream
        S8["active_domains (from Step 1 tail)"]:::xstream
        S9["scene_result.present_npcs<br>(from Step 2a)"]:::xstream
        S10["items_gained: list[str] (names)<br>items_lost: list[str] (ids)<br>(from Step 2b — minimal cross-stream)"]:::xstream
    end
```
Replace with:
```mermaid
    subgraph IN["Inputs"]
        S1["narrative (from Step 1)"]:::xstream
        S2["state.pc (name, bio, stats)"]
        S3["state.scene.recent_events"]
        S4["state.scene.world_state"]
        S5["active_quests (status=active only)"]
        S6["rules_outcome"]:::xstream
        S7["intent (from Step 0)"]:::xstream
        S8["active_domains (from Step 1 tail)"]:::xstream
        S9["recent_turns[-2:]<br>(T-1 + T-2 prior narration<br>for outcome_summary context)"]
        S10["items_gained: list[str] (names)<br>items_lost: list[str] (ids)<br>(from Step 2b — minimal cross-stream)"]:::xstream
    end
```

Current `Outputs` block (lines 297–303):
```mermaid
    subgraph OUT["Outputs — ProgressExtractResult"]
        O1["quest_updates: list[QuestUpdate]<br>  id, title, status,<br>  objectives[]: index, description,<br>  done, failed"]:::outNode
        O2["recent_events_add: list[str]"]:::outNode
        O3["recent_events_update: list[RecentEventUpdate]<br>  old, new"]:::outNode
        O4["recent_events_remove: list[str]"]:::outNode
        O5["compendium_npc_update: list[CompendiumNpcUpdate]<br>  id, name?, title?, bio?"]:::outNode
    end
```
Replace with:
```mermaid
    subgraph OUT["Outputs — ProgressExtractResult"]
        O1["quest_updates: list[QuestUpdate]<br>  id, title, status,<br>  objectives[]: index, description,<br>  done, failed"]:::outNode
        O2["recent_events_add: list[RecentEvent]<br>  id, text, turn"]:::outNode
        O3["recent_events_update: list[RecentEventUpdate]<br>  id, text"]:::outNode
        O4["recent_events_remove: list[str]"]:::outNode
        O5["actions: list[str]<br>  exactly 4 suggested player choices"]:::outNode
        O6["outcome_summary: str<br>  1–2 sentence narrative recap"]:::outNode
    end
```

Then update the closing note (currently lines 309–311):
```markdown
> **Always runs:** Progress is the post-narration storytelling brain. It always executes
> every turn (never skipped) and feeds next turn's rules call via `pending_gm_beat`,
> `recent_events_add`, and `scene_pressure_*`.
```
Replace with:
```markdown
> **Always runs:** Progress is the post-narration storytelling brain. It always executes
> every turn (never skipped) and feeds next turn's rules call via `recent_events_add`
> (durable narrative facts) and `quest_updates` (advancing or closing arcs). Scene-side
> forward signals (`scene_pressure_*`, `pending_gm_beat`) are sourced from the scene
> stream, not progress.
```

**Validation:** Inside the Step 2c `subgraph OUT` block, `compendium_npc_update` should not appear; `actions` and `outcome_summary` should appear. The closing note should no longer attribute `pending_gm_beat` to progress.

#### Step 06.4 — Fix the Delta Merge node and Cross-Pipeline arrows

**File:** `ccya/docs/ARCHITECTURE.md`

**What:** Two edits.

(a) The Delta Merge `MERGE` node (currently line 331):
```mermaid
    MERGE["StateDelta<br>──────────────────<br>scene_tags, scene_tagline<br>location_change, location_description<br>present_npcs<br>inventory_add / remove / update<br>pc_condition_add / remove<br>quest_updates<br>recent_events_add / update / remove<br>compendium_npc_update"]:::mergeNode
```
Replace with:
```mermaid
    MERGE["StateDelta<br>──────────────────<br>scene_tags, scene_tagline<br>location_change, location_description<br>npc_add / npc_remove / npc_update<br>compendium_npc_update<br>scene_pressure_add / remove / update<br>inventory_add / remove / update<br>pc_condition_add / remove<br>quest_updates<br>recent_events_add / update / remove<br><br>(gm_beat NOT in StateDelta —<br>written directly to state.meta.pending_gm_beat)"]:::mergeNode
```

(b) The Cross-Pipeline Data Flow diagram (currently around lines 466–479) has an edge:
```mermaid
    STEP2A -- "present_npcs" --> STEP2C
```
Delete that line entirely. Progress no longer receives `present_npcs` from scene.

Also, in the Step 1 outputs section of the same diagram, the line:
```mermaid
        N7["last_turn_failed<br>(precondition failures from prev turn)"]
```
should be deleted (currently inside Step 1's `Inputs` subgraph at line 141 of the file — verify by grep). The narrate context no longer reads `last_turn_failed`.

**Validation:** `grep -n 'present_npcs.*--> STEP2C' ccya/docs/ARCHITECTURE.md` — no matches. `grep -n 'last_turn_failed' ccya/docs/ARCHITECTURE.md` — no matches.

#### Step 06.5 — REPOMAP/state.md fix

**File:** `ccya/docs/REPOMAP/state.md`

**What:** Line 45 currently reads:
```yaml
  pending_gm_beat: dict | None  # GM beat from progress extractor, consumed by next turn's narrator (runtime-only, not in default state)
```
Replace with:
```yaml
  pending_gm_beat: dict | None  # GM beat from scene extractor, consumed by next turn's narrator (runtime-only, not in default state)
```

**Validation:** `grep -n "from scene extractor" ccya/docs/REPOMAP/state.md` — one match, on the `pending_gm_beat` line.

#### Step 06.6 — REPOMAP/engine.md fixes

**File:** `ccya/docs/REPOMAP/engine.md`

**What:** Two edits.

(a) The `_narrate_messages` signature line (currently line 70) lists `last_turn_failed=None,`. Remove it. The full updated signature line:
```markdown
- `_narrate_messages(env, state, user_input, *, chronicle_tail="", recent_turns=None, enable_narrate_thinking=False, pack_style="", narrator_rules=[], rules_outcome=None, npc_name_pool=None, recently_left=None, momentum=0, pending_gm_beat=None, deescalate=False, ages=None, known_npcs=None, present_npcs=None, world_factions=None, world_locations=None, pc_allegiance=None)` → `list[dict]` — prompt builder for narrator; accepts momentum, pending_gm_beat, deescalate, ages, known_npcs, present_npcs, world context params, and narrator_rules
```

(b) The `_run_extraction_pipeline` signature line (currently line 91) advertises a 7-tuple:
```markdown
- `_run_extraction_pipeline(env, state, narration, *, active_domains, rules_outcome=None, intent=None, config, trace_id, turn_no, deescalate=False, quest_ages=None, recent_turns=None)` → `tuple[StateDelta, list[str], str, list[str], dict, ProgressExtractResult, SceneExtractResult]` (async) — runs 3 streams in sequence (scene gated by active_domains, state gated by active_domains, progress always runs), transfer-verb scan activates inventory domain before state stream, dedup pre-pass redirects compendium NPC IDs before StateDelta merge, merges into StateDelta; returns 7-tuple including scene_result
```
Replace with:
```markdown
- `_run_extraction_pipeline(env, state, narration, *, active_domains, rules_outcome=None, intent=None, config, trace_id, turn_no, deescalate=False, quest_ages=None, recent_turns=None)` → `tuple[StateDelta, list[str], str, dict, ProgressExtractResult, SceneExtractResult]` (async) — runs 3 streams in sequence (scene gated by active_domains, state gated by active_domains, progress always runs), transfer-verb scan activates inventory domain before state stream, dedup pre-pass redirects compendium NPC IDs before StateDelta merge, merges into StateDelta; returns 6-tuple `(merged_delta, actions, outcome_summary, per_stream_event_data, progress_result, scene_result)`
```

**Validation:** `grep -n "last_turn_failed" ccya/docs/REPOMAP/engine.md` — no matches. `grep -n "7-tuple" ccya/docs/REPOMAP/engine.md` — no matches.

#### Step 06.7 — REPOMAP/testing.md fix

**File:** `ccya/docs/REPOMAP/testing.md`

**What:** Line 7 currently reads:
```markdown
- `test_engine_pipeline.py` — Token-budget ceilings, multi-turn invariants, scope-gating tests (Tier 1 eval harness)
```
Replace with:
```markdown
- `test_engine_pipeline.py` — Multi-turn invariants, scope-gating tests, dedup/transfer-verb tests (Tier 1 eval harness; token-budget ceilings are commented out per project owner direction)
```

**Validation:** `grep -n "Token-budget ceilings" ccya/docs/REPOMAP/testing.md` — no matches.

#### Step 06.8 — Plan-doc pointer fixes (×4)

**Files:**
- `ccya/docs/plans/eval-results-remediation/A-eval-results-remediation-pipeline-field-routing.md`
- `ccya/docs/plans/eval-results-remediation/B-eval-results-remediation-pressure-rules.md`
- `ccya/docs/plans/eval-results-remediation/C-eval-results-remediation-gm-beat-enforcement.md`
- `ccya/docs/plans/eval-results-remediation/D-eval-results-remediation-quest-state-extraction.md`

**What:** In each file, find every occurrence of `docs/REPOMAP/extraction.md` and replace with `docs/REPOMAP/engine.md`. (No such REPOMAP doc as `extraction.md` exists; engine internals live in `engine.md`.)

**Validation:** `grep -rn "REPOMAP/extraction.md" ccya/docs/plans/` — no matches.

#### Step 06.9 — TODO.md update

**File:** `ccya/docs/plans/TODO.md`

**What:** Two edits.

(a) Mark Plans A/B/C/D complete. Locate lines 71–74 (the four open bullets under P3):
```markdown
- **Pipeline field routing remediation** — `eval-results-remediation/A-eval-results-remediation-pipeline-field-routing.md` — route `actions`/`outcome_summary` to progress extractor, `compendium_npc_update`/`scene_pressure_*`/`gm_beat` to scene extractor, remove `failed` from state extractor
- **Scene pressure lifecycle rules** — `eval-results-remediation/B-eval-results-remediation-pressure-rules.md` — survival check for pressure removal, location-change guard, fixed-price transaction carve-out
- **GM beat quality enforcement** — `eval-results-remediation/C-eval-results-remediation-gm-beat-enforcement.md` — Pydantic validator nullifies beats with blank/generic instructions, strengthened prompt rule requiring named entity
- **Quest and state extraction fixes** — `eval-results-remediation/D-eval-results-remediation-quest-state-extraction.md` — contact/meet objective auto-completion, transfer-verb inventory domain trigger, NPC compendium dedup pre-pass
```
Replace with:
```markdown
- ~~**Pipeline field routing remediation** — `eval-results-remediation/A-eval-results-remediation-pipeline-field-routing.md` — route `actions`/`outcome_summary` to progress extractor, `compendium_npc_update`/`scene_pressure_*`/`gm_beat` to scene extractor, remove `failed` from state extractor~~
- ~~**Scene pressure lifecycle rules** — `eval-results-remediation/B-eval-results-remediation-pressure-rules.md` — survival check for pressure removal, location-change guard, fixed-price transaction carve-out~~
- ~~**GM beat quality enforcement** — `eval-results-remediation/C-eval-results-remediation-gm-beat-enforcement.md` — Pydantic validator nullifies beats with blank/generic instructions, strengthened prompt rule requiring named entity~~
- ~~**Quest and state extraction fixes** — `eval-results-remediation/D-eval-results-remediation-quest-state-extraction.md` — contact/meet objective auto-completion, transfer-verb inventory domain trigger, NPC compendium dedup pre-pass~~
- **Cleanup pass after Plans A–D** — `four-plans-cleanup/` — comment out token-budget ceilings, remove `failed` plumbing, scrub stale fixtures + dead Jinja, align ARCHITECTURE/REPOMAP/PROMPTING docs to post-Plan-A reality.
```

(b) Do NOT move the four plans to `docs/plans/completed/` in this phase. Archival is a separate operation; mark complete via strikethrough only, per AGENTS.md "abandoned items get struck through" pattern (the same convention applies to completed-but-not-archived items here).

**Validation:** `grep -n "four-plans-cleanup" ccya/docs/plans/TODO.md` — exactly one match.

#### Step 06.10 — Final cross-doc grep sanity sweep

**What:** Run these greps and confirm zero matches outside the eval-engine surface (which is intentionally untouched):
- `grep -rn "from progress extractor" ccya/docs/ ccya/ccya/` — must be empty in `ccya/docs/REPOMAP/` and `ccya/ccya/engine/`.
- `grep -rn "last_turn_failed" ccya/ccya/ ccya/docs/ ccya/tests/` — must be empty (eval files unchanged are fine; none currently match).
- `grep -rn "REPOMAP/extraction.md" ccya/docs/` — must be empty.
- `grep -rn "actions: list\[str\] (suggested" ccya/docs/ARCHITECTURE.md` — must be empty (the stale Step 2a output description).

### Tests to write or update
None (doc-only phase).

### REPOMAP updates required
All in steps 06.5–06.7 above.

### Risks
1. ARCHITECTURE.md mermaid block edits introduce a syntax error that breaks rendering. **Mitigation:** preserve existing class-name styling exactly; `:::xstream`, `:::outNode`, `:::mergeNode` already declared in the diagram's classDef block.
2. A future reader looks for the four remediation plans under `completed/` and doesn't find them. **Mitigation:** they are still discoverable via the strikethrough TODO entry; the `four-plans-cleanup` plan completion (when this plan itself ships) will trigger an archival pass.

---

## Tests to write or update (full plan summary)
All test edits live inside their respective phases. No net-new test files. Total test surface change:
- Phase 01: comment out 5 tests in `tests/test_engine_pipeline.py`.
- Phase 02: delete 2 tests + remove 1 kwarg from a third in `tests/test_engine_smoke.py`; remove 1 kwarg in `tests/test_prompt_audit.py`; remove 1 ctx key in `tests/test_names.py`.
- Phase 03: no test changes.
- Phase 04: rewrite 4 fixture/helper definitions across `tests/test_engine_smoke.py` and `tests/test_engine_pipeline.py`.
- Phase 05: no test changes either way.
- Phase 06: no test changes.

Final-phase command: `make check && make test`. Both must be green.

## TODO.md update
Captured in step 06.9.

## Out of scope (logged for the next eval-engine plan)
The following known-incorrect references in the eval surface are deliberately NOT touched here:
- `ccya/ccya/eval/runner.py` reads `state.scene.pending_gm_beat`; engine writes `state.meta.pending_gm_beat`.
- `ccya/ccya/eval/universal_asserts.py::check_pending_gm_beat_consumed` reads from `state.scene.pending_gm_beat`.
- `ccya/ccya/eval/engine_mirror.py` `KNOWN_ASSERT_FIELDS` puts `scene_pressure_add` under `extract.progress` (post-Plan-A it belongs under `extract.scene`); `state_yaml.pending_gm_beat.{present,absent}` paths point at `scene` not `meta`.
- `ccya/evals/scenarios/gm_beat_lifecycle.py` asserts use `state_yaml` paths that resolve against the wrong subtree.
- `ccya/evals/rubrics/default.md` line 10 still attributes `scene_pressure, gm_beat` to `extract.progress`.
- `ccya/evals/runs/*` historical artifacts predate the validators; safe to leave or sweep separately.
- Plan B asks for a `_FakeLLM` fixed-price transaction carve-out test; not added here. Plan D asks for a contact-objective completion test; not added here.

These items are pre-loaded for the next planning session and explicitly out of this plan.

## Ambiguities requiring resolution before execution
1. **Phase 05 option (a) vs (b)** — see the Phase 05 Ambiguities block. Executor must NOT proceed past Phase 04 until owner picks one.