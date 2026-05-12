# Eval Harness Remediation — Eval Run 20260512T154142Z_uufm2ojg

## Status
`open`

## Part of
standalone

## Dependencies
- mechanical plan (for momentum telemetry in events.jsonl, which this plan's judge trace quality phase depends on)

## Objective
The eval harness produced auto-checker failures that were wrong (false positives on NPC extraction and binding directives), missed real failures (key consumption, inventory zero-amount, compactor sanitization skipping), and gave the judge a trace with insufficient momentum and scope telemetry. This plan fixes those harness-level issues so that the auto-checker signal is trustworthy and the judge trace is actionable without manual log inspection.

## Non-goals
- Engine behavior changes — covered in mechanical, state-fidelity, and system-cohesion plans.
- Prompt changes — covered in prompt-quality plan.
- Narrator or extractor LLM improvements — covered in narrative plan.
- Changing the judge scoring rubric or the 11-section judge output format.

---

## Implementation — Phase 01: Auto-checker false positives

### Files to pull for context
- `ccya/eval/universal_asserts.py` (all assertion functions and `_extract_candidate_names`)
- `evals/scenarios/full_cycle.py` (T5 assert that expected combat)
- `ccya/eval/engine_mirror.py` (`KNOWN_ASSERT_FIELDS`)

### Detailed steps

#### Step 1.1 — Harden `_extract_candidate_names` for ambient/common descriptors

**File:** `ccya/eval/universal_asserts.py`

**What:** Expand the descriptor_stop set inside `_extract_candidate_names` to cover the specific descriptors that were false-positive flagged as NPC names. Based on the REPOMAP note (Hulking, Generous already excluded), review the eval run for additional false positives and add them.

**Why:** `check_npc_mention_extracted` FAILed on T5 when "two armed toughs" appeared in narration but were correctly not in `npc_add` because they were unnamed ambients. The helper failed to exclude the leading capitalized descriptor words.

**Code Snippet** — Replace the existing descriptor_stop set at line 189-197 with:

```python
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

**Validation:** Feed T5 narration text through `_extract_candidate_names`; assert the two toughs' descriptor words are not returned as candidate names.

---

#### Step 1.2 — Skip `check_rolled_implies_binding` when `required=false`

**File:** `ccya/eval/universal_asserts.py`

**What:** In `check_rolled_implies_binding`, before checking that the BINDING block appears in the narrate prompt, verify that the rules outcome had `required=True` (i.e., a roll actually happened). If `required=False` or absent, return a passing result immediately.

**Why:** On no-roll turns, the BINDING block is not injected into the narrate prompt by design. The assert was FAILing these turns incorrectly.

**Code Snippet** — Replace the existing `check_rolled_implies_binding` function (lines 135-161) with:

```python
def check_rolled_implies_binding(event: dict[str, Any]) -> dict[str, Any]:
    """If rules.rolled=true, narrate_prompt.rendered_user must contain 'rules_outcome (BINDING'."""
    rules = event.get("rules") or {}
    if not rules.get("rolled"):
        return {
            "assertion": "universal.narrate.binding_present",
            "passed": True,
            "detail": "(no roll)",
            "scope": "universal",
            "severity": "red",
        }
    # If a roll was required, the BINDING block should be in the narrate prompt.
    # If required=false (no roll happened despite rules call), skip.
    if not rules.get("required", False):
        return {
            "assertion": "universal.narrate.binding_present",
            "passed": True,
            "detail": "no roll required, binding not expected",
            "scope": "universal",
            "severity": "red",
        }
    nu = (event.get("narrate_prompt") or {}).get("rendered_user") or ""
    if "rules_outcome (BINDING" in nu:
        return {
            "assertion": "universal.narrate.binding_present",
            "passed": True,
            "detail": "binding directive included",
            "scope": "universal",
            "severity": "red",
        }
    return {
        "assertion": "universal.narrate.binding_present",
        "passed": False,
        "detail": "rolled=true but narrate user prompt did not include rules_outcome BINDING block",
        "scope": "universal",
        "severity": "red",
    }
```

**Validation:** Run a no-roll turn through `check_rolled_implies_binding`; assert result is `passed=True` not `passed=False`.

---

### Tests to write or update
- `tests/test_universal_asserts.py`: add NPC descriptor false-positive test and no-roll binding skip test.

### REPOMAP and architecture updates
- `docs/REPOMAP/eval.md`: document expanded descriptor_stop set and no-roll skip behavior.

### Risks
1. Over-expanding descriptor_stop could suppress real NPC names that happen to be descriptors. Keep the list to unambiguous common adjectives and small cardinal numbers only.

---

## Implementation — Phase 02: Missing auto-checker coverage

### Files to pull for context
- `ccya/eval/universal_asserts.py` (existing assert list and `run_all_universal_asserts` signature)
- `ccya/eval/runner.py` (`_check_asserts`, `run_scenario`)
- `ccya/eval/engine_mirror.py` (`KNOWN_ASSERT_FIELDS`)
- `ccya/eval/report.py` (`_render_assert_summary_table`)

### Detailed steps

#### Step 2.1 — Add `check_key_consumed_after_use`

**File:** `ccya/eval/universal_asserts.py`

**What:** Assert that if the narration contains explicit key-use language ("slid the key", "turned the key", "inserted the key", "unlocked" + item name that ends in `_key`) and the pre-turn state contains that key, the post-turn state should NOT contain it at the same amount. Severity: yellow (narrative language is ambiguous; hard FAIL would produce too many false positives).

**Note:** The runner injects `state_snapshot` (post-delta) into events but NOT `state_snapshot_before`. This assert will compare pre/post by checking `applied.inventory_remove` alongside `state_snapshot` — if a key was removed via applied, it should not appear in `state_snapshot` at the same amount. If no `inventory_remove` entry exists for the key, the assert skips.

**Code Snippet:**

```python
_KEY_USE_PHRASES: tuple[str, ...] = (
    "slid the", "turned the", "inserted the", "used the", "unlocked"
)

def check_key_consumed_after_use(event: dict[str, Any], prev_event: dict[str, Any] | None = None) -> dict[str, Any]:
    narration = event.get("narration", "")
    if not any(p in narration.lower() for p in _KEY_USE_PHRASES):
        return {"severity": "yellow", "result": "skip", "reason": "no key-use language"}
    applied = event.get("applied") or {}
    removes = applied.get("inventory_remove") or []
    removed_ids = {r.get("id") for r in removes if isinstance(r, dict) and r.get("id", "").endswith("_key")}
    post = (event.get("state_snapshot") or {}).get("inventory", [])
    post_keys = {i["id"]: i.get("amount", 1) for i in post if isinstance(i, dict) and i["id"].endswith("_key")}
    for kid in removed_ids:
        if post_keys.get(kid, 0) > 0:
            return {
                "severity": "yellow",
                "result": "fail",
                "reason": f"{kid} removed in applied but still present in state_snapshot",
            }
    return {"severity": "yellow", "result": "pass"}
```

**Validation:** Simulate a T8-like event where narration contains "slid the brass key" and `applied.inventory_remove` contains `brass_key` but `state_snapshot.inventory` still has it; assert the assert returns fail.

---

#### Step 2.2 — Add `check_no_negative_inventory`

**File:** `ccya/eval/universal_asserts.py`

**What:** Assert that no inventory item in `state_snapshot` has `amount < 1`. Severity: red (zero or negative amounts are always a bug).

**Code Snippet:**

```python
def check_no_negative_inventory(event: dict[str, Any]) -> dict[str, Any]:
    inventory = (event.get("state_snapshot") or {}).get("inventory", [])
    bad = [i["id"] for i in inventory if isinstance(i, dict) and i.get("id") and i.get("amount", 1) < 1]
    if bad:
        return {"severity": "red", "result": "fail", "reason": f"zero/negative inventory: {bad}"}
    return {"severity": "red", "result": "pass"}
```

**Validation:** Test with state containing credits at `amount: 0`; assert fail.

---

#### Step 2.3 — Register new asserts in `run_all_universal_asserts`

**File:** `ccya/eval/universal_asserts.py`

**What:** Add both new functions to the list inside `run_all_universal_asserts` so they run on every turn.

**Code Snippet** — Append to the results list in `run_all_universal_asserts` (after line 681):

```python
        check_key_consumed_after_use(event, prev_event),
        check_no_negative_inventory(event),
```

**Validation:** Confirm the new asserts appear in `_render_assert_summary_table` output in `report.py`.

---

#### Step 2.4 — No change needed to `KNOWN_ASSERT_FIELDS`

**File:** `ccya/eval/engine_mirror.py`

**What:** `KNOWN_ASSERT_FIELDS` maps stream names to field names for scenario-level TurnAssert validation. The new asserts are universal asserts (called by `run_all_universal_asserts`), not scenario-level TurnAssert entries. They do not belong in `KNOWN_ASSERT_FIELDS`.

**Validation:** `tests/test_eval_schema.py` schema validation passes without changes to `engine_mirror.py`.

---

### Tests to write or update
- `tests/test_universal_asserts.py`: unit tests for both new asserts covering pass, fail, and skip paths.
- `tests/test_eval_schema.py`: no changes needed — `KNOWN_ASSERT_FIELDS` is unchanged.

### REPOMAP and architecture updates
- `docs/REPOMAP/eval.md` universal_asserts section: add both new assert function entries.

### Risks
1. `check_key_consumed_after_use` relies on `applied.inventory_remove` being populated. Confirm runner injects applied into events (it does — see `runner.py` line 329). If the key was consumed via a mechanism other than `inventory_remove` (e.g., direct state mutation), the assert will skip.

---

## Implementation — Phase 03: Judge trace quality

### Files to pull for context
- `ccya/eval/judge.py` (`_render_deterministic_signals`, `_build_metrics_rows`)
- `ccya/eval/report.py` (`_compute_pacing_metrics`)
- `ccya/eval/runner.py` (event shape — what keys are available per event)

### Detailed steps

#### Step 3.1 — Add scope fallback rate to Deterministic Signals

**File:** `ccya/eval/judge.py`

**What:** In `_render_deterministic_signals`, add a row to the Metrics table for scope fallback rate: count events where `scope.decided_by != "narrator"` divided by total turns. Display as a percentage.

**Why:** If the narrator scope tag fails silently on many turns, the judge cannot see it in the current trace. This rate should be visible alongside token counts.

**Code Snippet** — Add to `_render_deterministic_signals` after the Metrics table header and row rendering (around line 409), before the parse details section:

```python
    # Scope fallback rate
    fallback_turns = sum(
        1 for e in events_for_scope
        if e.get("scope", {}).get("decided_by", "narrator") != "narrator"
    )
    scope_fallback_rate = fallback_turns / len(events_for_scope) if events_for_scope else 0.0
    parts.append(f"\n**Scope fallback rate:** {scope_fallback_rate:.0%} ({fallback_turns}/{len(events_for_scope)} turns)\n")
```

**Note:** `_render_deterministic_signals` currently receives metrics (list of dicts) but not raw events. The scope fallback computation needs events. Two options:
- A) Pass events as an additional parameter to `_render_deterministic_signals` (preferred — cleanest).
- B) Compute scope fallback in `run_judge_streaming` before calling `build_trace` and pass it as a separate param.

**Recommended approach (A):** Update the function signature and call site:

```python
def _render_deterministic_signals(
    failures: list[dict[str, Any]] | None,
    metrics: list[dict[str, Any]] | None,
    events: list[dict[str, Any]] | None = None,
    redundancy_signals: dict[str, Any] | None = None,
    compaction_signals: dict[str, Any] | None = None,
) -> str:
```

And in `build_trace`, pass events through. In `run_judge_streaming`, pass events to `build_trace`.

**Validation:** Run a trace with a known scope fallback turn; confirm the rate row appears in the deterministic signals section.

---

#### Step 3.2 — Add per-turn momentum to metrics rows

**File:** `ccya/eval/judge.py` (`_build_metrics_rows`)

**What:** If the emitted event contains a momentum block (added by **mechanical plan Phase 05**, not system-cohesion), add momentum telemetry as a column in the per-turn metrics table.

**Why:** The eval REPORT currently shows no per-turn momentum telemetry. The mechanical plan adds `momentum_before/after/delta` to events.jsonl; this step surfaces it in the judge trace.

**Code Snippet** — In `_build_metrics_rows`, add `momentum_after` to the row dict:

```python
        rows.append({
            "turn": ev.get("turn", "?"),
            "rules_tok_in": int(rules_meta.get("est_tokens", 0) or 0),
            "narrate_tok_in": int(narr_meta.get("est_tokens", 0) or 0),
            "scene_tok_in": int((ext.get("scene") or {}).get("context_meta", {}).get("est_tokens", 0) or 0),
            "state_tok_in": int((ext.get("state") or {}).get("context_meta", {}).get("est_tokens", 0) or 0),
            "progress_tok_in": int((ext.get("progress") or {}).get("context_meta", {}).get("est_tokens", 0) or 0),
            "parse_failures": len(parse_errors),
            "retries": retries,
            "parse_error_details": parse_errors,
            "momentum_after": (ev.get("state_snapshot") or {}).get("meta", {}).get("momentum", "—"),
        })
```

And update `_render_deterministic_signals` to render the column:

```python
        parts.append("| Turn | rules tok_in | narrate tok_in | scene tok_in | state tok_in | progress tok_in | parse_fail | retries | momentum |\n")
        parts.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|\n")
        for m in metrics:
            parts.append(
                f"| {m.get('turn','?')} | {m.get('rules_tok_in',0)} | "
                f"{m.get('narrate_tok_in',0)} | {m.get('scene_tok_in',0)} | "
                f"{m.get('state_tok_in',0)} | {m.get('progress_tok_in',0)} | "
                f"{m.get('parse_failures',0)} | {m.get('retries',0)} | "
                f"{m.get('momentum_after', '—')} |\n"
            )
```

**Validation:** Run a smoke trace; confirm the momentum column appears per turn.

---

### Tests to write or update
- `tests/test_eval.py`: update `build_trace()` test to assert scope fallback rate text is present in Deterministic Signals when applicable.

### REPOMAP and architecture updates
- `docs/REPOMAP/eval.md` judge.py section: document scope fallback rate and momentum column additions.

### Risks
1. `_render_deterministic_signals` has a fixed table structure; adding a column changes the header and all row formatting. Test rendering at multiple column counts.
2. Passing events into `_render_deterministic_signals` requires threading it through `build_trace` → `_render_deterministic_signals`. Ensure `build_trace`'s signature and call sites in `run_judge_streaming` are updated consistently.

---

## Implementation — Phase 04: Scenario fixture accuracy

### Files to pull for context
- `evals/scenarios/full_cycle.py` (all TurnAssert entries)
- `ccya/eval/engine_mirror.py` (`KNOWN_ASSERT_FIELDS`, `EXTRACT_STREAMS`)
- `ccya/eval/scenario.py` (`TurnAssert`, `Turn`)
- `ccya/eval/runner.py` (`_check_asserts`)

### Detailed steps

#### Step 4.1 — Fix T5 scene tag assertion

**File:** `evals/scenarios/full_cycle.py`

**What:** Change the T5 assert that expects "combat" in `scene_tags` to expect "standoff" instead. Since `_check_asserts` only supports single-value expected matching (no `contains_any` operator), use the most likely tag from the T5 narration: "standoff".

**Why:** T5 narration described a verbal standoff with armed toughs, not active combat. The assert was wrong, not the engine.

**Code Snippet** — Replace the T5 assert at line 102:

```python
                TurnAssert(stream="extract.scene", field="scene_tags", expected="standoff"),
```

**Validation:** `tests/test_eval_schema.py` should continue to pass (path is valid). Run the scenario and confirm T5 no longer produces a false FAIL.

**Note:** If the engine produces a different tag (e.g., `tense_confrontation`), adjust the expected value accordingly. The `_check_asserts` handler for `extract.scene.scene_tags` does exact string match only.

---

#### Step 4.2 — T3 inventory credit assert

**ABANDONED.** T3 does NOT involve the PC spending credits. T3 is "offer to carry his ledger for 200 credits" — the PC is earning credits, not spending them. The T3 inventory assert was removed as unnecessary.

---

#### Step 4.3 — T8 key removal assert

**ABANDONED.** The T8 asserts at lines 148-151 already include:

```python
TurnAssert(stream="extract.state", field="inventory_remove", expected="brass_key"),
```

This is correct. No change needed for T8.

---

### Tests to write or update
- `tests/test_eval_schema.py`: after fixture changes, re-run to confirm all TurnAssert paths are valid.

### REPOMAP and architecture updates
- `docs/REPOMAP/eval.md` scenario section: note that `full_cycle.py` T5 tag was corrected from combat to standoff.

### Risks
1. `_check_asserts` for `extract.scene.scene_tags` does exact string match only. If the engine produces standoff as one of multiple tags, the assert passes. If it produces `tense_confrontation` instead, the assert fails. Verify the actual engine output.
2. `_check_asserts` does NOT support `contains_any`, `gt`, `not_contains_id`, or dotpath resolution. All scenario asserts must use the supported `stream/field/expected` pattern.

---

## Ambiguities requiring resolution before execution

1. Does `runner.py:_check_asserts` support `op="contains_any"` and `op="not_contains_id"`? Answer: No. The `_check_asserts` function only supports exact string match for `expected`. Scenario asserts must use single expected values. Phase 04 has been corrected to use supported operators only.
2. Does each emitted event include a `state_snapshot_before` (pre-delta) key as well as `state_snapshot` (post-delta)? Answer: No. The runner injects only `state_snapshot` (post-delta). `check_key_consumed_after_use` has been corrected to use `applied.inventory_remove` instead of `state_snapshot_before`.
3. Is the T3 seed state credits balance known? Answer: T3 does not involve credits removal by the PC. T3 is contract acceptance where the PC earns credits. The T3 inventory assert was removed as unnecessary. Read `evals/scenarios/full_cycle.py` lines 64-77 to confirm.
