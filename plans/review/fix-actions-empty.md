# Fix: Progress Extractor Returns Empty actions[]

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Diagnose root cause | Determine why actions is consistently empty across all 13 turns |
| 02 | Fix schema instruction and/or Python default | Enforce non-empty actions in schema prompt and model validation |

## Objective
The progress extractor's `actions` field returns an empty array on every turn across a 13-turn eval run. `actions` is defined in `ProgressExtractResult` and is expected to return exactly 4 player choice strings per turn. This breaks the front-end action buttons. The root cause is unknown — it could be a schema instruction deficiency, a model validation gap, or a Python-side default that silently swallows the field.

## Non-goals
- Do not change the meaning of `actions` — it should remain exactly 4 ~10-word player choices.
- Do not alter any other field in `ProgressExtractResult`.
- Do not change the extraction pipeline control flow.

## Implementation — Phase 01: Diagnose root cause

### Files to pull for context
- `ccya/models.py` — find `ProgressExtractResult` and confirm field definition for `actions`.
- `ccya/prompts/extract_progress_system.j2` — confirm `actions` field rule text (already read; see schema block).
- `ccya/prompts/extract_progress_user.j2` — confirm `actions` appears in the user prompt context (present_npcs, active_threads, band, stakes are all relevant inputs).
- `ccya/engine/extraction.py` — `_extract_progress_messages()` and `_run_extraction_pipeline()` to confirm `progress_result.actions` is passed through correctly.
- `ccya/engine/turn.py` — confirm `actions` from `progress_result.actions` is stored in the turn result.

### Detailed steps

#### Step 1.1 — Confirm ProgressExtractResult.actions field type in models.py

**File:** `ccya/models.py`

**What:** Read the `ProgressExtractResult` class. Confirm the `actions` field type annotation. If it is `list[str] = []` (a mutable default), check if Pydantic silently drops the field on parse when the LLM omits it from the JSON.

**Why:** Pydantic will use the default `[]` if the field is absent from the LLM's JSON response. If the LLM is consistently omitting `actions`, the Python side will silently return `[]` with no warning. This is a silent fallback — exactly what AGENTS.md prohibits.

**Validation:** Inspect the field definition. If it is `list[str] = []`, this is the silent-default pattern.

#### Step 1.2 — Check extract_progress_user.j2 for missing actions-enabling context

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** Read the full template. Confirm that `present_npcs`, `active_threads`, `pc_stats`, and `band` are rendered. If the template renders empty sections for these (e.g., `present_npcs` is always `[]` when the progress prompt runs, because `_ExtractionContext.present_npcs_this_turn` is empty), the model has nothing to ground actions on and may omit the field or return empty.

**Why:** The `actions` schema instruction in `extract_progress_system.j2` requires: one choice advancing an active thread, one involving a present NPC, one leveraging the PC's highest stat, one freeform. If `active_threads` is empty and `present_npcs` is empty, the model cannot satisfy 3 of 4 constraints and may bail entirely.

**Validation:** Simulate the context for a mid-game turn. Check if `active_threads` and `present_npcs` are non-empty when passed to `_extract_progress_messages()`.

#### Step 1.3 — Check if actions is stripped by _parse_stream_result

**File:** `ccya/engine/extraction.py` — `_parse_stream_result()` and `_call_stream()` for progress.

**What:** Confirm `strip_keys=("_reasoning",)` is what is passed when calling progress. Confirm `actions` is NOT in `strip_keys`. If it is, that is the bug.

**Validation:** Grep `strip_keys` usage for the progress call in `_run_extraction_pipeline`. Confirm `actions` is never in any strip list.

### Tests to write or update
None for Phase 01 — read-only diagnosis.

### REPOMAP and architecture updates
None.

### Risks
1. The model is responding with `actions` but it is being stripped or overwritten downstream — mitigation: also check `turn.py` for any code that resets or ignores `progress_result.actions`.

## Implementation — Phase 02: Fix schema instruction and model validation

### Files to pull for context
- `ccya/models.py` — `ProgressExtractResult`.
- `ccya/prompts/extract_progress_system.j2`.
- `ccya/prompts/extract_progress_user.j2`.

### Detailed steps

#### Step 2.1 — Add validator to ProgressExtractResult.actions

**File:** `ccya/models.py`

**What:** If `actions` is `list[str] = []`, add a `field_validator` that warns when `actions` is empty at parse time. Do NOT raise — the turn must not fail. But log a warning so the problem surfaces in logs.

```python
from pydantic import field_validator
import logging
_log = logging.getLogger(__name__)

class ProgressExtractResult(BaseModel):
    actions: list[str] = []
    # ... other fields ...

    @field_validator("actions")
    @classmethod
    def warn_empty_actions(cls, v: list[str]) -> list[str]:
        if not v:
            _log.warning(
                "progress.actions is empty — LLM omitted field or returned []",
                extra={"turn": 0, "trace_id": "", "pack": "", "kind": "extraction"},
            )
        return v
```

**Why:** Makes the silent-default problem visible in logs without breaking the turn.

**Validation:** Unit test: parse a `ProgressExtractResult` from JSON with `actions` absent. Confirm the validator fires (can assert log output with `caplog`).

#### Step 2.2 — Reinforce actions instruction in extract_progress_system.j2

**File:** `ccya/prompts/extract_progress_system.j2`

**What:** The current `actions` rule says "exactly 4 distinct player choices". Add a MUST-NOT-OMIT sentence immediately after:

```
`actions`: exactly 4 distinct player choices, ~10 words each, drawn from THIS turn's narration and current arc state. Structure: one choice should advance an active thread, one should involve an NPC who is present in the scene, one should leverage the PC's highest stat value (do NOT mention stat directly), and one should be a distinct exploration/environmental or freeform option not covered by the other three. Weight toward thread objectives and motivations. Each should move the plot forward substantially in a different direction. Examples: "Aim for the chest and fire", "Convince the guard to let you pass". Bias to bold, good storytelling choices. **You MUST always emit exactly 4 non-empty strings in this field. Never emit an empty array.**
```

**Why:** Models are more likely to omit optional-looking fields. Making the constraint explicit and imperative reduces omission rate.

**Validation:** Re-run the eval or smoke test with the modified prompt. Confirm `actions` is non-empty.

#### Step 2.3 — Verify extract_progress_user.j2 renders non-empty NPC and thread sections

**File:** `ccya/prompts/extract_progress_user.j2`

**What:** Read the template. If `present_npcs` and `active_threads` are guarded by `{% if %}` blocks that produce empty sections when the lists are empty (possible on turn 1), add fallback copy:

```jinja2
{% if present_npcs %}
### Present NPCs
{% for n in present_npcs %}- {{ n.name or n.id }}{% if n.title %} ({{ n.title }}){% endif %}
{% endfor %}
{% else %}
### Present NPCs
None currently tracked. Generate actions that could involve any NPC mentioned in the narration.
{% endif %}
```

**Why:** If the template silently outputs nothing for these sections, the model has no grounding for NPC-based and thread-based actions and skips the field.

**Validation:** Render the template with empty `present_npcs` and `active_threads`. Confirm the output contains fallback text rather than empty sections.

### Tests to write or update
- `tests/test_prompt_audit.py` or `tests/test_engine_smoke.py`: assert that `result.actions` is non-empty after a smoke turn with valid state.
- `tests/test_engine_pipeline.py`: add a `TurnAssert` that checks `len(result.actions) == 4` for every turn in a multi-turn sequence.

### REPOMAP and architecture updates
- `docs/REPOMAP/models.md`: note the `warn_empty_actions` validator on `ProgressExtractResult.actions`.

### Risks
1. The validator added in Step 2.1 may cause mypy issues if `_log` is not defined at module scope in `models.py` — mitigation: confirm `models.py` imports `logging` before adding.
2. Modifying the system prompt may shift other field behavior — mitigation: only append to the existing `actions` rule; do not restructure surrounding fields.

## Ambiguities requiring resolution before execution
1. Is `ProgressExtractResult.actions` defined as `list[str] = []` or something else (e.g., `list[str] = Field(default_factory=list)`)? Options: A) simple default — validator approach works. B) custom validator already present — check what it does before adding another.
2. Is `extract_progress_user.j2` even rendering `active_threads` and `present_npcs`? Options: A) Yes, but they may be empty at turn 1. B) No — they are missing from the template entirely, in which case Step 2.3 becomes an addition, not a conditional fix.
