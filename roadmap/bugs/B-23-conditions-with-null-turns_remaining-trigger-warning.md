---
title: "Conditions with null turns_remaining trigger warning — Pydantic doesn't coerce None to default"
status: canceled
canceled: 2026-06-29
canceled_reason: "Superseded by B-24 (consolidated extraction reliability ticket). Fix applied via validator in models/state.py."
type: bug
urgency: 3
size: small
created: 2026-06-29
ticket_id: B-23
labels: [conditions, pydantic, extraction]
superseded_by: roadmap/bugs/B-24-extraction-reliability-null-fields-missing-required-data.md
---

## Description

When the LLM outputs `null` for `turns_remaining` on a condition, Pydantic v2 sets it to `None` instead of using the default `0`. The `_expire_conditions` function then sees `None`, which doesn't match `isinstance(tr, int)` or `tr == "permanent"`, triggering:

```
condition unknown turns_remaining type: NoneType for <condition_id>
```

This was observed with `tremors` (noir-1930s) and `hunted` (zombie-survival) conditions during Phase 3 eval.

## Root Cause

`Condition` and `ConditionAdd` models have `turns_remaining: int | Literal["permanent"] = 0` but no validator to handle `None`. Pydantic v2 accepts `null` from JSON and sets `None` instead of falling back to the default.

## Fix

Added `@field_validator("turns_remaining", mode="before")` to both `Condition` and `ConditionAdd` models in `models/state.py` to coerce `None` → `0`.

## Verification

```python
>>> Condition(id='tremors', label='Tremors', turns_remaining=None)
turns_remaining=0
>>> ConditionAdd(id='hunted', label='Hunted', turns_remaining=None)
turns_remaining=0
```

## Files Changed

- `ccya/models/state.py` — Added `_coerce_tr` validator to `Condition` and `ConditionAdd`
