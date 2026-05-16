# fix-drift-analysis-coercion

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | DriftAnalysis field coercion | Add `field_validator` on `ProgressExtractResult.drift_analysis` to remap `id` → `thread_id` and tolerate missing `thread_id` |
| 02 | CompactorSanitizationResult pressure_remove coercion | Add `field_validator` on `CompactorSanitizationResult.pressure_remove` (and peers) to coerce bare strings into `{"id": ..., "confidence": "high"}` dicts |

## Objective
Two recurring Pydantic parse failures are silently discarding all `extract_progress` output on every turn and all compactor sanitization on compaction turns. The first is that the LLM consistently returns `drift_analysis` items with a top-level `id` field (matching the pattern for `thread_signals`) rather than the schema-required `thread_id`. `ProgressExtractResult` already coerces `thread_signals` via `_map_thread_id_to_id`, but no equivalent validator exists for `drift_analysis`. The second is that the compactor LLM returns `pressure_remove` (and sometimes `inventory_remove`, `condition_remove`) as bare strings like `"tough_a"` instead of `{"id": "tough_a", "confidence": "high"}` objects, failing `CompactorSanitizationAction` validation.

## Non-goals
- No changes to prompts or prompt templates.
- No changes to how `DriftAnalysis` or `CompactorSanitizationAction` are used downstream — coercion only at parse boundary.
- No changes to the compactor's application logic (`_apply_sanitization`).
- No retry-prompt changes in `_call_stream`.

---

## Implementation — Phase 01: DriftAnalysis field coercion

### Files to pull for context
- `ccya/models.py` — `DriftAnalysis`, `ProgressExtractResult`, `_map_thread_id_to_id` validator on `thread_signals`

### Detailed steps

#### Step 1.1 — Add `_coerce_drift_analysis` validator to `ProgressExtractResult`

**File:** `ccya/models.py`

**What:** Add a `field_validator("drift_analysis", mode="before")` on `ProgressExtractResult` that iterates the list and, for each dict item, renames `id` → `thread_id` if `thread_id` is absent. Also silently drops any item that has neither field so a partial LLM response doesn't abort the whole parse.

**Why:** The LLM (Gemma-4-26B-A3B, Qwen3.6-35B) consistently emits `{"id": "settle_the_debt", "match": true, ...}` instead of `{"thread_id": "settle_the_debt", "match": true, ...}`. Pydantic `mode="before"` lets us normalise the raw dict before field-level validation. The pattern is identical to the existing `_map_thread_id_to_id` on `thread_signals`.

**Code Snippet**
```python
@field_validator("drift_analysis", mode="before")
@classmethod
def _coerce_drift_analysis(cls, v: Any) -> Any:
    if not v:
        return v
    if not isinstance(v, list):
        return v
    out = []
    for item in v:
        if isinstance(item, dict):
            if "thread_id" not in item:
                if "id" in item:
                    item = dict(item)
                    item["thread_id"] = item.pop("id")
                else:
                    # No usable identity key — skip rather than fail the whole parse
                    continue
            out.append(item)
        elif isinstance(item, DriftAnalysis):
            out.append(item)
    return out
```

Place this validator immediately after `_map_thread_id_to_id` (the `thread_signals` validator) in the `ProgressExtractResult` class body.

**Validation:** After the change, run the eval with `make eval`. The `extract_progress parse failed` lines for `drift_analysis.N.thread_id Field required` should be gone across all 13 turns. Confirm with `grep -c 'drift_analysis' evals/runs/<latest>/events.jsonl` (expect 0 error entries containing that key).

### Tests to write or update

**File:** `tests/test_models.py` (create if absent; add to existing otherwise)

Test function: `test_drift_analysis_coerces_id_to_thread_id`
- Build a raw dict list: `[{"id": "thread_a", "match": True, "reason": "matched"}, {"id": "thread_b", "match": False}]`
- Construct `ProgressExtractResult(drift_analysis=raw)` — must not raise.
- Assert `result.drift_analysis[0].thread_id == "thread_a"`.
- Assert `result.drift_analysis[1].thread_id == "thread_b"`.

Test function: `test_drift_analysis_drops_items_with_no_id`
- Raw: `[{"match": True, "reason": "no id here"}]`
- Construct `ProgressExtractResult(drift_analysis=raw)` — must not raise.
- Assert `result.drift_analysis == []`.

Test function: `test_drift_analysis_passthrough_when_thread_id_present`
- Raw: `[{"thread_id": "thread_a", "match": True}]`
- Assert coercion does not mutate — `result.drift_analysis[0].thread_id == "thread_a"`.

### REPOMAP and architecture updates
`docs/REPOMAP/models.md` — note the new `_coerce_drift_analysis` validator on `ProgressExtractResult`.

### Risks
1. The `DriftAnalysis` model could receive `thread_id=None` if `id` is an empty string — mitigated by the `continue` guard (empty string still sets thread_id to `""`, which Pydantic will accept as a `str`; downstream code ignores empty-id items already).
2. If a future schema change renames the field again, this silently swallows it — acceptable because the validator logs nothing; if needed a debug log can be added.

---

## Implementation — Phase 02: CompactorSanitizationResult string coercion

### Files to pull for context
- `ccya/models.py` — `CompactorSanitizationAction`, `CompactorSanitizationResult`
- `ccya/engine/compactor.py` — `_parse_compact_response`, `_apply_sanitization`

### Detailed steps

#### Step 2.1 — Add coercion validators to `CompactorSanitizationResult`

**File:** `ccya/models.py`

**What:** Add `field_validator` (mode `"before"`) on each of `inventory_remove`, `pressure_remove`, and `condition_remove` in `CompactorSanitizationResult` that converts bare strings to `{"id": str, "confidence": "high"}` dicts. The `npc_merge` field takes `CompactorNpcMerge` objects (different shape), so it is not touched here.

**Why:** The log shows:
```
compactor: invalid sanitization payload, skipping: 2 validation errors for CompactorSanitizationResult
pressure_remove.0
  Input should be a valid dictionary or instance of CompactorSanitizationAction [type=model_type, input_value='tough_a', input_type=str]
```
The LLM emits `"pressure_remove": ["tough_a", "tough_b"]` instead of `[{"id": "tough_a", "confidence": "high"}, ...]`. Rather than fix in the prompt (AGENTS.md prohibits prompt changes unless explicitly requested), coerce at the model boundary.

**Code Snippet**
```python
def _coerce_sanitization_actions(v: Any) -> Any:
    if not v:
        return v
    out = []
    for item in v:
        if isinstance(item, str):
            out.append({"id": item.strip(), "confidence": "high"})
        else:
            out.append(item)
    return out


class CompactorSanitizationResult(BaseModel):
    npc_merge: list[CompactorNpcMerge] = Field(default_factory=list)
    inventory_remove: list[CompactorSanitizationAction] = Field(default_factory=list)
    pressure_remove: list[CompactorSanitizationAction] = Field(default_factory=list)
    condition_remove: list[CompactorSanitizationAction] = Field(default_factory=list)
    recent_events_compact: list[CompactorRecentEventCompact] = Field(default_factory=list)

    model_config = {"extra": "ignore"}

    @field_validator("inventory_remove", "pressure_remove", "condition_remove", mode="before")
    @classmethod
    def _coerce_actions(cls, v: Any) -> Any:
        return _coerce_sanitization_actions(v)
```

Place `_coerce_sanitization_actions` as a module-level helper immediately before `CompactorSanitizationResult`. Replace the current `CompactorSanitizationResult` class body with the above (preserving all existing fields and `model_config`).

**Validation:** Run `make eval`. The `compactor: invalid sanitization payload, skipping` warning should not appear. If compaction fires (turn divisible by `compact_every`), the sanitization block in the event record should be non-null.

### Tests to write or update

**File:** `tests/test_models.py`

Test function: `test_compactor_sanitization_coerces_string_pressure_remove`
- Build: `CompactorSanitizationResult(pressure_remove=["tough_a", "tough_b"])` — must not raise.
- Assert `result.pressure_remove[0].id == "tough_a"` and `result.pressure_remove[0].confidence == "high"`.
- Assert `result.pressure_remove[1].id == "tough_b"`.

Test function: `test_compactor_sanitization_coerces_string_inventory_remove`
- Same pattern with `inventory_remove=["old_sword"]`.

Test function: `test_compactor_sanitization_passthrough_dict`
- `pressure_remove=[{"id": "tough_a", "confidence": "medium"}]` — confirm `confidence == "medium"` (not overwritten by coercer).

### REPOMAP and architecture updates
`docs/REPOMAP/models.md` — note `_coerce_sanitization_actions` helper and the new validator on `CompactorSanitizationResult`.

### Risks
1. `_coerce_sanitization_actions` is a module-level function — ensure it is defined before `CompactorSanitizationResult` in the file (Python evaluates class bodies top-to-bottom).
2. `npc_merge` items are `CompactorNpcMerge` (requires `keep_id` + `remove_ids`) — do not apply this coercer to `npc_merge`; string coercion would produce nonsense.

## Ambiguities requiring resolution before execution
*(none — both failure modes are deterministic from the log)*
