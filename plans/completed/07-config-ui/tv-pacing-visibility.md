# TV pacing mechanics visibility fixes

## Status
`completed`

## Phases

1 phase: Extract pacing_context into turn viewer row data so the template displays new pacing mechanics correctly. Enhance state_diff thread_add display to show dedup key field. Add momentum_before/momentum_after from structured ruling event to left panel pipeline view as outcome metrics alongside intent fields.

## Issue

The turn viewer's right panel has a "Pacing Context" section (`ccya/templates/_turn_viewer.html` lines 265-293) that expects `t.pacing_context` with fields directive, gate, beat_hint, and beat_locked — but Python code in `_turn_viewer_data()` never extracts pacing_context from events into the row dict. The entire section is always empty. Additionally:

1. Template references non-existent field `beat_hint` (events.jsonl only has directive/beat_locked/gate/summary).
2. ArcThread `.key` field (`ccya/models.py` line 58) — used for dedup at thread_add time — is buried inside the dict dump in state_diff and never explicitly surfaced to help verify auto-merge behavior.
3. `momentum_after` from structured ruling event outcome (`ev["ruling"]`) is visible only if users expand the ruling prompt/output tab; not shown as a summary metric alongside intent/intent_verb/target/check.

## Solution

Extract pacing_context directly from events.jsonl into the turn viewer row dict (it's written at `turn.py` line 1506). Replace template's `beat_hint` reference with `summary`. Enhance `_tv_state_diff` to explicitly show ArcThread.key when present on thread_add entries. Extract momentum_before/momentum_after from structured ruling event (`ev["ruling"]`) and display them in the left panel pipeline view as outcome metrics alongside intent fields.

Note: consecutive_pressure_turns is NOT included — it lives only in game state under `state["meta"]["consecutive_pressure_turns"]` which runner.py merges into turn_events for eval purposes, not into raw events.jsonl that tv.py reads. Users can infer pressure tracking from pacing_context directive value ("Pressure"/"Threat Pressure") and beat_locked=true signal without the raw counter.

## Firm decisions

1. pacing_context is extracted from `ev["pacing_context"]` — it's written directly into every events.jsonl entry at turn.py line 1506 with keys: directive, beat_locked, gate, summary.
2. ArcThread.key is optional (`ccya/models.py` line 58: `key: str | None = None`). Only show in state_diff when non-null and non-empty.
3. momentum_before/momentum_after come from the structured ruling event (`ev["ruling"]`), NOT from IntentEnvelope/rules stream output which only has intent/intent_verb/target/check (`ccya/models.py` lines 166-170). Extract via `_get_nested(ev, "ruling.momentum_after")`.
4. momentum delta display goes into the left panel ruling dl section (`ccya/templates/_turn_viewer.html` lines 195-205), not the right diff panel, because it's a ruling outcome metric like intent/intent_verb/target/check.

## Non-goals

- Do NOT add new CSS classes or styling — reuse existing `tv-diff-row`, `tv-diff-field`, `tv-diff-value` patterns for diff section; use `<dt>/<dd>` syntax matching the existing dl section for ruling panel.
- Do NOT modify any pipeline code (`turn.py`, `extraction.py`, `narrate.py`). Only server/tv.py and ccya/templates/_turn_viewer.html change.
- Do NOT add ArcThread.key to thread_advance or thread_resolve entries — only thread_add where the key is most relevant for dedup verification.
- Do NOT show pacing_context.summary in a separate section; it replaces beat_hint within the existing Pacing Context block.
- Do NOT extract consecutive_pressure_turns — not available in events.jsonl, would require either modifying turn.py to include it or loading state.yaml per-event which is outside scope.

## Risks, Ambiguities, and Blockers

1. **Template rules_intent vs ruling_intent mismatch**: The template's dl section (line 195) checks `t.rules_intent` but Python only sets `"ruling_intent"` in the row dict (`tv.py` line 562). Step 1.5 must either create an alias or fix the template to use the correct field name for momentum display.
2. **No tests to run**: Per AGENTS.md, tests are temporarily removed during refactor phase. Only `make check` runs as final validation.

## Implementation — Phase 1: TV pacing mechanics visibility

### Context files to load
- `ccya/server/tv.py` (full file, 611 lines)
- `ccya/templates/_turn_viewer.html` (lines 78–320 for turn card rendering section)
- `ccya/models.py` line 58 (ArcThread.key definition), lines 166-170 (IntentEnvelope schema)

### Detailed steps

#### Step 1.1 — Extract pacing_context into row dict

**File:** `ccya/server/tv.py`

**What:** In `_turn_viewer_data()`, add `"pacing_context": ev.get("pacing_context") or {}` to the row dict at line ~567 (inside the rows.append block, after `"failures"` and before `"prompts"`). pacing_context is written directly into every events.jsonl entry by turn.py line 1506 with keys: directive, beat_locked, gate, summary.

**Why:** The template (`ccya/templates/_turn_viewer.html` lines 265-293) expects `t.pacing_context` to exist but Python never populates it. Without this extraction the entire Pacing Context section is always empty regardless of pacing mechanics firing.

**Validation:** No new imports or function signatures change. Just one key added to an existing dict literal.

#### Step 1.2 — Extract momentum_before/momentum_after from structured ruling event into row dict

**File:** `ccya/server/tv.py`

**What:** In `_turn_viewer_data()`, add `"momentum_delta"` and `"momentum_after"` to the same rows.append block, extracted from the structured ruling event:
```python
"momentum_before": int(_get_nested(ev, "ruling.momentum_before") or 0),
"momentum_after": int(_get_nested(ev, "ruling.momentum_after") or 0),
```

**Why:** momentum_before/momentum_after are in the structured ruling event (`ev["ruling"]` at turn.py lines 1485-1487) which IS written to events.jsonl. They are NOT part of IntentEnvelope/rules stream output (which only has intent/intent_verb/target/check). The template dl section needs these values to show the momentum delta as an outcome metric alongside intent fields.

**Validation:** Uses existing `_get_nested` helper from tv_mirror.py. Falls back to 0 if ruling event or momentum keys are absent. Does not modify any pipeline code — only reads data already in events.jsonl.

#### Step 1.3 — Enhance _tv_state_diff to show ArcThread.key on thread_add entries

**File:** `ccya/server/tv.py`

**What:** In `_tv_state_diff()`, modify the thread_add handling block (lines 247-256). When building value_str for a dict-valued thread_add entry, extract and prepend the key field if present:
```python
tid = val.get("id", "?")
tkey = val.get("key") or ""
tsummary = val.get("summary", "")[:80]
scope_tag = f"[{val.get('scope', '?')}]"
if tkey and isinstance(tkey, str) and tkey.strip():
    value_str = f"{tid} [{tkey}] {scope_tag}: {tsummary}"
else:
    value_str = f"{tid} {scope_tag}: {tsummary}"
```

**Why:** ArcThread.key (`ccya/models.py` line 58) is the canonical concept label used for dedup at thread_add time with auto-merge on collision. Users need to see this key explicitly in state_diff to verify whether dedup/gate logic correctly prevents duplicate threads from being added. Currently it's buried inside any dict dump and not visible as a structured field.

**Validation:** Only affects the value_str display for thread_add entries. Does not change op, field, or rejected status. Thread objects without key fall through to existing format unchanged.

#### Step 1.4 — Update template: replace beat_hint with summary in Pacing Context section

**File:** `ccya/templates/_turn_viewer.html`

**What:** In the Pacing Context section (lines 265-293):
1. Change line 265 condition from `(t.pacing_context.directive || t.pacing_context.gate !== 'allow' || t.pacing_context.beat_hint)` to `(t.pacing_context.directive || t.pacing_context.gate !== 'allow')` — remove the beat_hint check so section shows whenever pacing_context has directive or non-allow gate.
2. Replace lines 280-285 (beat_hint template block) with a summary block:
```html
<template x-if="t.pacing_context.summary">
    <div class="tv-diff-row">
        <span class="tv-diff-field">summary</span>
        <span class="tv-diff-value" x-text="t.pacing_context.summary"></span>
    </div>
</template>
```

**Why:** `beat_hint` never exists in events.jsonl pacing_context (turn.py only writes directive/beat_locked/gate/summary). The section condition on line 265 will always evaluate to false when beat_hint is the only truthy field, hiding the entire section. Replacing with summary shows actual pacing outcome text from turn.py's _pc.summary.

**Validation:** Template syntax must remain valid Alpine.js. No new CSS classes needed — reuses existing tv-diff-row/tv-diff-field/tv-diff-value pattern.

#### Step 1.5 — Add momentum delta to ruling dl section in left panel pipeline view

**File:** `ccya/templates/_turn_viewer.html`

**What:** In the ruling intent dl section (lines 195-205), after the check block and before the closing `</dl>`, add:
```html
<template x-if="t.momentum_after != null && t.momentum_before != null">
    <dt>momentum</dt><dd class="tv-inline-json" x-text="(t.momentum_before ?? '?') + ' → ' + (t.momentum_after ?? '?')"></dd>
</template>
```

**Why:** momentum_before/momentum_after are ruling outcome metrics that should be visible alongside intent/intent_verb/target/check in the left panel pipeline view. Currently users must expand the full ruling prompt/output JSON to see them. Showing as "X → Y" makes delta visible at a glance without requiring expansion of the raw output tab. Uses proper `<dt>/<dd>` syntax matching the existing dl section (not custom span classes).

**Validation:** Uses `t.momentum_after` and `t.momentum_before` which Python extracts from structured ruling event (`ev["ruling"]`) in Step 1.2. Falls back to null/empty if ruling event or momentum keys are absent. Matches the `<dt>/<dd>` pattern used by intent/intent_verb/target/check entries above it.

### Tests to write or update
None — tests are temporarily removed during refactor phase per AGENTS.md. Run `make check` as final validation only.

### REPOMAP updates required
- `docs/repomap.md` section on turn viewer (`tv.py`): Add pacing_context extraction, momentum_before/momentum_after extraction from structured ruling event, ArcThread.key display to the list of what `_turn_viewer_data` extracts from events.jsonl into row dict. Update template section description to note summary replaces beat_hint in Pacing Context block and momentum delta added to ruling dl section.
