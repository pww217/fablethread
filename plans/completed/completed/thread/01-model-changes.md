# Phase 1 — Model changes

## Purpose

Update `ArcThread` and `ThreadUpdate` models with new `type` field, replace `active` with `dormant`, and remove `"dormant"` from urgency Literal.

## Problem Statement

The source models must match the new design before any consuming code can use the new fields. Without these changes, all downstream phases have no foundation.

## Constraints

- Phase 1 must not break the existing test suite (no tests currently, but must not introduce syntax/validation errors).
- Backwards compat: old JSON state with `active` field must coerce cleanly to `dormant`.

## Non-goals

- No changes to consuming code (turn.py, sanitizer, prompts, etc.) — that is Phase 3+.
- No changes to ArcThreadSummary (it's in context.py, covered in Phase 6).

## Solution

Add `type` field, replace `active` with `dormant`, remove `"dormant"` from urgency Literal on both `ArcThread` and `ThreadUpdate`, and add a backwards-compat model_validator.

## Firm decisions

1. `dormant: bool = False` replaces `active: bool = True`.
2. Backwards compat: `active: True → dormant: False`, `active: False → dormant: True`.
3. Unknown/source-missing values default to `dormant: False`.
4. `urgency` Literal stays `["background", "normal", "urgent"]` — source already has this shape, no change needed.
5. Both `type` fields are `Literal["threat", "opportunity", "complication", "revelation"] | None = None`.
6. ThreadUpdate drops `active` in favor of `dormant: bool | None = None`.
7. Both models keep `model_config = {"extra": "ignore"}`.

## Risks, Ambiguities, and Blockers

- **Backwards compat is a one-time migration.** Old state JSON files with `active` must not crash on load. The `model_validator(mode="before")` handles this, but it only applies when the model is validated from a dict. If old state is loaded through a different path (e.g., raw JSON merge in delta_builder), the coercion might not fire. Check all call sites that construct or validate ArcThread/ThreadUpdate from external data.
- **`_validate_parsed()` in thread_sanitizer.py** calls `ThreadUpdate.model_validate(tu_copy)` — this will trigger the model_validator. Good.
- **`_enforce_thread_limits()` in seed.py** mutates threads via `object.__setattr__` — those mutations set `active` directly on model instances. After Phase 1, those `__setattr__` calls will fail because `active` no longer exists. Phase 2 fixes this.
- **Source does NOT have "dormant" in the urgency Literal** — `Literal["background", "normal", "urgent"]` (3 values, not 4). No Literal changes needed.

### Detailed steps

#### Step 1.1 — Add `type` field to `ArcThread`

**File:** `ccya/models.py:35-48`

**What:** Add `type: Literal["threat", "opportunity", "complication", "revelation"] | None = None` after the `urgency` field on `ArcThread`. Do NOT change the urgency Literal — source already has `Literal["background", "normal", "urgent"]` which is correct.

**Why:** Enables semantic classification of threads by the storyteller. Optional field for backwards compat.

**Validation:** `.venv/bin/python -c "from ccya.models import ArcThread; t = ArcThread(id='t1', summary='test'); assert t.type is None; t2 = ArcThread(id='t2', summary='test', type='threat'); assert t2.type == 'threat'"`

#### Step 1.2 — Replace `active` with `dormant` on `ArcThread`

**File:** `ccya/models.py:35-48`

**What:** Remove `active: bool = True`. Add `dormant: bool = False` before `urgency`. Add a `@model_validator(mode="before")` classmethod `_coerce_active_to_dormant` that reads `active` from raw dict and maps it to `dormant` (`active=True → dormant=False`, `active=False → dormant=True`). Runs before field validation so old data coerces cleanly.

```python
@model_validator(mode="before")
@classmethod
def _coerce_active_to_dormant(cls, data: Any) -> Any:
    if isinstance(data, dict):
        if "active" in data and "dormant" not in data:
            data["dormant"] = not data.pop("active")
    return data
```

(`model_validator` is already imported at line 12 of models.py.)

**Why:** `active` was ambiguous (latent vs. dormant vs. background). `dormant` is semantically clear. Validator ensures old saves don't crash.

**Validation:** `.venv/bin/python -c "from ccya.models import ArcThread; t = ArcThread.model_validate({'id':'t1','summary':'x','active':True}); assert t.dormant == False; t2 = ArcThread.model_validate({'id':'t2','summary':'x','active':False}); assert t2.dormant == True; t3 = ArcThread.model_validate({'id':'t3','summary':'x','dormant':True}); assert t3.dormant == True"`

### Tests to write or update

No tests currently. Run `make check` after phase to confirm no lint/type errors.

## Status

completed
