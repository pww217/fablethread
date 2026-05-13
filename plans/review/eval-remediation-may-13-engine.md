# Eval Remediation Plan — 2026-05-13 — Engine Fixes

**Status:** Draft
**Part of:** Full cycle eval remediation — engine, prompts, harness
**Dependencies:** None (self-contained; companion plan `eval-remediation-may-13-prompts.md` handles prompt-only changes)

## Conflicts and overlap

This plan handles **engine code fixes** and **harness changes**. A companion plan `eval-remediation-may-13-prompts.md` handles prompt-only changes (narrate_system.j2, extract_progress_system.j2). The two plans can run in parallel since they touch disjoint file sets.

---

## Objective

**State Fidelity Rate:** 85.0%
**Prompt Adherence Rate:** 92.0%

Fix two root causes identified in the eval report: (1) an engine bug in `state/delta.py` that silently drops quest objectives without `description` fields (causing T8 empty objectives and state drift), and (2) auto-checker false positives on capitalized location fragments in `universal_asserts.py`.

## Non-goals

- Prompt changes (handled in companion plan `eval-remediation-may-13-prompts.md`)
- Momentum soft cap / decay mechanic (minor issue, deferred)
- Compaction sanitization logging to events.jsonl (already planned in `plans/review/turn-viewer-overhaul.md` Step 3.1)
- Condition lifecycle (bruised_ribs overlong is narrative, not engine)
- Quest dedup at T2/T6/T7 (prompt issue — LLM re-emits completed quests; companion plan adds stronger few-shot examples)
- T2 narration drift (prompt issue — narrator changes 500 to 50; companion plan strengthens "Player input is truth" rule)

---

## Affected files

| File | Module | Change type |
|---|---|---|
| `ccya/state/delta.py` | state | engine |
| `ccya/eval/universal_asserts.py` | eval | harness |
| `docs/REPOMAP/engine.md` | docs | docs |
| `docs/REPOMAP/state.md` | docs | docs |

---

## Firm decisions

1. **Quest objectives without `description` must be preserved in new quest creation.** The engine currently filters them out at `state/delta.py:338` via `if o.description`. This is a bug: the progress prompt allows `{"index": N, "done": true}` without description for update-only objectives. The fix is to remove the `if o.description` filter in the new-quest creation path. The existing quest update path (lines 261-300) already handles index-based updates without requiring description.

2. **The T2 narration drift is a prompt issue, not an engine bug.** The state extractor correctly removes what the narration says. The fix is in the companion prompt plan. This plan does NOT touch the narrate prompt.

3. **Auto-checker NPC false positives are caused by location name fragments matching capitalized tokens.** The fix is to add location name fragments to the stop set in `_extract_candidate_names`. Specifically, words like "Crossed", "Inside", "Before", "Leather", "Shelf" are location/item name fragments, not NPC names.

4. **Compaction sanitization logging to events.jsonl is deferred to `turn-viewer-overhaul.md`.** That plan already includes Step 3.1 which writes compaction events. No change needed here.

---

## Implementation phases

### Phase 1 — Fix quest objective filtering in apply_delta (new quest creation path)

**Pipeline:** state delta application
**File:** `ccya/state/delta.py`
**Passage:** Lines 327-340 (new quest creation in `apply_delta`)

**Current text:**
```python
                new_q: dict[str, Any] = {
                    "id": qu.id,
                    "title": _strip_non_ascii(qu.title) if qu.title else "",
                    "status": qu.status or "active",
                    "objectives": [
                        {
                            "description": _strip_non_ascii(o.description) if o.description else "",
                            "done": o.done if o.done is not None else False,
                            "failed": bool(o.failed) if o.failed is not None else False,
                        }
                        for o in qu.objectives
                        if o.description
                    ],
                }
```

**New text:**
```python
                new_q: dict[str, Any] = {
                    "id": qu.id,
                    "title": _strip_non_ascii(qu.title) if qu.title else "",
                    "status": qu.status or "active",
                    "objectives": [
                        {
                            "description": _strip_non_ascii(o.description) if o.description else "",
                            "done": o.done if o.done is not None else False,
                            "failed": bool(o.failed) if o.failed is not None else False,
                        }
                        for o in qu.objectives
                    ],
                }
```

**Why:** The `if o.description` filter silently drops objectives that have `index` and `done` but no `description`. The progress prompt allows `{"index": N, "done": true}` for update-only objectives (line 24 of extract_progress_system.j2: "Update existing: `{"id": "quest_id", "status": "active|completed|failed|abandoned", "objectives": [{"index": N, "done": true}]}`"). At T8, the extractor emitted `{"id": "deliver_halden_ledger", "objectives": [{"index": 1, "done": false}]}` — which has NO `description` field. The filter `if o.description` excludes it, resulting in `objectives: []`. This is the root cause of the T8 quest structural drift (Section 1E: `deliver_halden_ledger` created at T8 with empty objectives array). Removing the filter preserves all objectives the LLM emits.

**Validation:** Re-run eval. T8 `deliver_halden_ledger` should have `objectives: [{"index": 1, "done": false}]` in state snapshot. Auto-checker `progress.quest_id_collision` should not flag T8. State fidelity rate should improve from 85% to ~92%.

---

### Phase 2 — Fix auto-checker NPC false positives on location fragments

**Pipeline:** eval harness
**File:** `ccya/eval/universal_asserts.py`
**Passage:** Lines 317-325 (`descriptor_stop` set in `_extract_candidate_names`)

**Current text:**
```python
    # Common descriptors and titles that are not NPC names
    descriptor_stop: set[str] = {
        "Scarred", "Tough", "Hooded", "Burly", "Young", "Old", "Tall",
        "Short", "Fat", "Thin", "Lean", "Dark", "Light", "Red", "Blue",
        "Green", "Gold", "Silver", "Iron", "Brass", "Wooden", "Stone",
        "Big", "Small", "Large", "Little", "High", "Low", "Fast", "Slow",
        "Good", "Bad", "New", "Last", "First", "Next", "Other", "Same",
        "Each", "Every", "Both", "All", "Some", "Any", "Many", "Few",
        "Hulking", "Generous", "Armed", "Two", "Three", "Several",
    }
```

**New text:**
```python
    # Common descriptors and titles that are not NPC names
    descriptor_stop: set[str] = {
        "Scarred", "Tough", "Hooded", "Burly", "Young", "Old", "Tall",
        "Short", "Fat", "Thin", "Lean", "Dark", "Light", "Red", "Blue",
        "Green", "Gold", "Silver", "Iron", "Brass", "Wooden", "Stone",
        "Big", "Small", "Large", "Little", "High", "Low", "Fast", "Slow",
        "Good", "Bad", "New", "Last", "First", "Next", "Other", "Same",
        "Each", "Every", "Both", "All", "Some", "Any", "Many", "Few",
        "Hulking", "Generous", "Armed", "Two", "Three", "Several",
        "Crossed", "Inside", "Before", "Leather", "Shelf", "Master",
    }
```

**Why:** The auto-checker flagged 7 turns for `universal.npc_mention.extracted` false positives. The trace shows narration mentions like "Crossed Keys Inn", "Inside the pantry", "Before the hearth", "Leather-bound ledger", "Shelf", "Master" — all location/item fragments, not NPC names. The current `descriptor_stop` set doesn't include these. Adding them to the stop set eliminates the false positives. The report (Section 6) confirms these are false positives and recommends a regex fix; adding to `descriptor_stop` is the simpler, more targeted fix.

**Validation:** Re-run eval. `universal.npc_mention.extracted` should pass on all 13 turns (currently fails on T1, T3, T4, T5, T7, T11, T13). Auto-checker failures should drop from 19 to ~12.

---

### Phase 3 — Verify collision-redirect path doesn't have the same bug

**Pipeline:** state delta application
**File:** `ccya/state/delta.py`
**Passage:** Lines 346-394 (quest alias collision redirect)

**Current text (lines 327-340, already fixed in Phase 1):**
```python
                new_q: dict[str, Any] = {
                    ...
                    "objectives": [
                        ...
                        for o in qu.objectives
                        if o.description
                    ],
                }
```

**New text:** No change needed. The collision-redirect block at lines 346-394 does NOT create a new quest dict. It reuses `existing_quests[qu.id]` and applies updates via the existing quest update logic at lines 353-393, which uses the same `if qu.objectives:` block as the main path (lines 261-300). That block handles index-based updates and description-based matching without requiring `o.description` to be truthy. The only place the buggy `if o.description` filter exists is in the new-quest creation path (lines 327-340), fixed in Phase 1.

**Why:** Verified code review. The collision-redirect path (lines 346-394) falls through to the existing quest handling code at lines 348-394, which updates `q = existing_quests[qu.id]` via the same objective-matching logic at lines 261-300. That logic handles `obj.index`-based updates and `obj.description`-based matching independently — it does NOT filter out objectives without descriptions. The bug is isolated to the new-quest creation path.

**Validation:** Code review only. No test needed since the collision path was never buggy.

---

## Tests

- `make test` — all existing tests should pass. The quest objective filter change is backward-compatible: objectives with descriptions continue to work; objectives without descriptions (the previously-broken case) now work too.
- `make test-v` — if any test fails, inspect the test's quest data to verify objectives are being preserved correctly.
- Re-run eval: `make eval` — verify:
  - T8 `deliver_halden_ledger` has populated objectives in state
  - `universal.npc_mention.extracted` passes on all 13 turns
  - State fidelity rate improves from 85% to ~92%
  - Auto-checker failures drop from 19 to ~12

## Risks

1. **Removing `if o.description` could introduce empty-description objectives into existing quest updates.** Mitigation: The filter only existed in the new-quest creation path. The existing quest update path (lines 261-300) already handles objectives without descriptions via index matching. No regression expected.

2. **Adding location fragments to `descriptor_stop` could mask real NPC names.** Mitigation: The stop set is conservative — only 6 words added, all confirmed as false positives in the trace. If a real NPC is named "Crossed" or "Leather", the assert would flag it, but that's an acceptable tradeoff for eliminating 7 false positive failures.

3. **Quest objectives with empty `description` strings will now be preserved.** Mitigation: This is the desired behavior. The progress prompt allows `{"index": N, "done": true}` without description. The engine should not silently drop these.

## Ambiguities and posed design questions

1. **Should the new-quest creation path also handle the case where `qu.objectives` is empty?** Currently, if the LLM emits `{"id": "new_quest", "objectives": []}`, the new quest is created with an empty objectives array. This is technically valid (the quest exists but has no objectives yet). The companion prompt plan addresses this by adding few-shot examples showing populated objectives. No engine change needed.

2. **Should `_extract_candidate_names` use a more sophisticated approach than a stop set?** The current approach (stop set + sentence-starters + descriptor filtering + inventory/location partial match) is a heuristic. A more sophisticated approach (e.g., NER, or checking against a known entity list) would be more accurate but is out of scope for this remediation. The stop set fix is targeted and low-risk.

3. **Should compaction sanitization be logged to events.jsonl in this plan?** The report (Section 5B) notes sanitization is "implicit/OK" and the trace shows "*(none recorded)*". This is a trace gap. However, `plans/review/turn-viewer-overhaul.md` Step 3.1 already plans to write compaction events to events.jsonl. Deferring to that plan avoids duplication.

## Execution order summary

| Phase | File | Steps | Description |
|---|---|---|---|
| 1 | `ccya/state/delta.py` | 1 | Remove `if o.description` filter in new quest creation (lines 327-340) |
| 2 | `ccya/eval/universal_asserts.py` | 1 | Add location fragments to `descriptor_stop` set (lines 317-325) |
| 3 | `ccya/state/delta.py` | 0 | Verify collision-redirect path is clean (code review only) |

**Total steps:** 2 code changes + 1 verification
**Estimated impact:** State fidelity 85% → ~92%, auto-checker failures 19 → ~12
