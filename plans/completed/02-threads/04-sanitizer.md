# Phase 4 — Sanitizer code + prompt

## Purpose

Update the thread sanitizer to handle `type` and `dormant` fields in `_apply_sanitization()`, and update `sanitize_thread.j2` with explicit abandonment criteria, type correction, dormant guidance, and culling guidance.

## Problem Statement

`_apply_sanitization()` iterates over fields `("active", "urgency")` and applies them. `active` is removed. The sanitizer prompt has no instructions about dormant, type, abandonment criteria, or culling. The sanitizer cannot correct bad type assignments or manage dormant threads effectively.

## Constraints

- Sanitizer prompt density must not increase unreasonably — replace or consolidate existing instructions where possible.
- Sanitizer output JSON examples must match the new Pydantic model shapes exactly.

## Non-goals

- No changes to `_validate_parsed()` — Pydantic handles the new fields automatically via `ThreadUpdate.model_validate()`.
- No changes to seed, turn processing, or convergence — covered in other phases.

## Solution

Update `_apply_sanitization()` to handle `type` and `dormant` alongside `active`/`urgency`. Update `sanitize_thread.j2` with abandonment criteria, type correction, dormant guidance, and culling guidance.

## Firm decisions

1. Sanitizer can set `type` and `dormant` on threads via `thread_updates` in its JSON output.
2. Sanitizer-triggered culls must generate a real outcome sentence from narrative evidence (unlike engine culls which use a mechanical fallback).
3. Abandonment criteria: no narrative mention in 5+ turns AND no activity in 3+ turns, with narrative justification required.
4. Sanitizer output JSON validation automatically coerces `type` and `dormant` via ThreadUpdate.model_validate.

## Risks, Ambiguities, and Blockers

- **Old sanitizer state:** Existing saves may have sanitizer state that references `active`. The backwards compat validator on ThreadUpdate handles old `active` → `dormant` mapping (added in Phase 1). No additional migration needed.
- **Prompt density:** The sanitizer prompt is 111 lines. Adding 4 new instruction sections may require consolidating existing ones. Consider removing the "temporal decay" section (line 47) which is now superseded by engine auto-dormant + sanitizer abandonment criteria.

## Status

`open`

## Implementation — Phase 4: Sanitizer code + prompt

### Context files to load

- `ccya/engine/thread_sanitizer.py:293-409` — `_apply_sanitization()`
- `ccya/prompts/sanitize_thread.j2:36-73` — Instructions section

### Detailed steps

#### Step 4.1 — Add `type` and `dormant` to sanitizer field iteration

**File:** `ccya/engine/thread_sanitizer.py:372-380`

**What:** Extend the field iteration tuple from `("active", "urgency")` to `("dormant", "urgency", "type")`. The loop body at lines 373-380 already handles arbitrary fields generically (`val = _tu.get(field)`), so extending the tuple is sufficient.

```python
for field in ("dormant", "urgency", "type"):
    val = _tu.get(field)
    if val is not None and val != getattr(arc.threads[found_idx], field):
        updates_dict[field] = val
        delta["fields"].append({
            "field": field,
            "before": getattr(arc.threads[found_idx], field),
            "after": val,
        })
```

Remove `"active"` from the tuple.

**Why:** Sanitizer must be able to update `type` (type correction) and `dormant` (dormant guidance) on threads. `active` is removed.

**Validation:** `.venv/bin/python -c "import ast; ast.parse(open('ccya/engine/thread_sanitizer.py').read()); print('syntax OK')"`

#### Step 4.2 — Update sanitizer prompt with new instructions

**File:** `ccya/prompts/sanitize_thread.j2`

**What:** Replace the "Instructions" section (lines 36-73) with:

1. **Abandonment criteria** (replaces line 47 "Temporal decay"): "If a thread has no narrative mention in 5+ turns AND no activity (progress/urgency change) in 3+ turns, consider resolving as abandoned. Abandonment requires narrative justification — do not abandon threads that are still relevant to the current situation."
2. **Type correction** (new): "If a thread's assigned type no longer matches its narrative role, update the type field."
3. **Dormant guidance** (new): "If a thread has no activity in 4+ turns, consider setting dormant: True."
4. **Culling guidance** (new): "If there are >= 3 dormant threads, consider resolving the oldest (by last_updated_turn) as abandoned with a narrative outcome sentence."
5. Update the "Per-thread checks" list to reference `dormant` instead of `active` for (de)activation.
6. Update the output JSON schema section to include `dormant` and `type` fields in the example.

**Why:** LLM needs explicit instructions to emit the new fields correctly. Removing "active" prevents confusion.

**Validation:** Manual inspection. No automated test for prompt text.

#### Step 4.3 — Remove old temporal decay section from sanitizer prompt

**File:** `ccya/prompts/sanitize_thread.j2:47`

**What:** Remove or rewrite the "Temporal decay" paragraph (currently says "inactive (active=false) threads with no progress for 3+ turns"). Replace with the new abandonment criteria instruction from Step 4.2.

**Why:** The old temporal decay guidance references `active=false` and a 3-turn threshold — both superseded by the new abandonment criteria (5+ turns no mention + 3+ turns no activity + narrative justification) and engine auto-dormant (4 turns).

**Validation:** Manual inspection of prompt output.

### Tests to write or update

No tests currently. Run `make check` for type/lint.

## Status

completed
