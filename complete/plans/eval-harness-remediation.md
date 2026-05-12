# Eval Harness Remediation — Eval Run 20260512T154142Z_uufm2ojg

## Status
`open`

## Phase Guide
| Phase | Name | Summary |
|---|---|---|
| 01 | Auto-checker false positives | Fix `check_npc_mention_extracted` over-flagging and `check_rolled_implies_binding` on no-roll turns |
| 02 | Missing auto-checker coverage | Add asserts for key consumption, inventory zero-amount, compactor sanitization nonzero, and stale immediate pressure |
| 03 | Judge trace quality | Reduce trace noise: scope tag failure rate, momentum telemetry row, pressure staleness signal in Deterministic Signals |
| 04 | Scenario fixture accuracy | Correct T5 `check_action` expectation from `combat` to a tension tag; add missing T3/T8 inventory assertions |

## Objective
The eval harness produced auto-checker failures that were wrong (false positives on NPC extraction and binding directives), missed real failures (key consumption, inventory zero-amount, compactor sanitization skipping), and gave the judge judge a trace with insufficient momentum and scope telemetry. This plan fixes those harness-level issues so that the auto-checker signal is trustworthy and the judge trace is actionable without manual log inspection.

## Non-goals
- Engine behavior changes — covered in mechanical, state-fidelity, and system-cohesion plans.
- Prompt changes — covered in prompt-quality plan.
- Narrator or extractor LLM improvements — covered in narrative plan.
- Changing the judge scoring rubric or the 11-section judge output format.

---

## Implementation — Phase 01: Auto-checker false positives

### Files to pull for context
- `ccya/eval/universal_asserts.py` (all assertion functions and `_extract_candidate_names`)
- `evals/scenarios/full_cycle.py` (T5 assert that expected `combat`)
- `ccya/eval/engine_mirror.py` (`KNOWN_ASSERT_FIELDS`)

### Detailed steps

#### Step 1.1 — Harden `_extract_candidate_names` for ambient/common descriptors

**File:** `ccya/eval/universal_asserts.py`

**What:** Expand the exclusion list in `_extract_candidate_names` to cover the specific descriptors that were false-positive flagged as NPC names. Based on the REPOMAP note (`Hulking`, `Generous` already excluded), review the eval run for additional false positives and add them.

**Why:** `check_npc_mention_extracted` FAILed on T5 when "two armed toughs" appeared in narration but were correctly not in `npc_add` because they were unnamed ambients. The helper failed to exclude the leading capitalized descriptor words.

**Code Snippet**
```python
_COMMON_DESCRIPTORS: frozenset[str] = frozenset({
    "Hulking", "Generous", "Armed", "Scarred", "Tall", "Short",
    "Young", "Old", "Robed", "Hooded", "Cloaked", "Masked",
    "Two", "Three", "Several", "Some", "A", "The",
})
```

In `_extract_candidate_names`, after sentence-initial capital exclusion, also filter tokens whose title-cased form is in `_COMMON_DESCRIPTORS`.

**Validation:** Feed T5 narration text through `_extract_candidate_names`; assert the two toughs' descriptor words are not returned as candidate names.

---

#### Step 1.2 — Skip `check_rolled_implies_binding` when `required=false`

**File:** `ccya/eval/universal_asserts.py`

**What:** In `check_rolled_implies_binding`, before checking that the BINDING block appears in the narrate prompt, verify that the rules outcome had `required=True` (i.e., a roll actually happened). If `required=False`, return a passing result immediately.

**Why:** On no-roll turns, the BINDING block is not injected into the narrate prompt by design. The assert was FAILing these turns incorrectly.

**Code Snippet**
```python
def check_rolled_implies_binding(event: dict, prev_event: dict | None, **_) -> dict:
    rules = event.get("rules", {})
    if not rules.get("required", False):
        return {"severity": "yellow", "result": "skip", "reason": "no roll, binding not expected"}
    # ... existing binding-block check ...
```

**Validation:** Run a no-roll turn through `check_rolled_implies_binding`; assert result is `"skip"` not `"fail"`.

---

### Tests to write or update
- `tests/test_universal_asserts.py`: add NPC descriptor false-positive test and no-roll binding skip test.

### REPOMAP and architecture updates
- `docs/REPOMAP/eval.md`: document `_COMMON_DESCRIPTORS` exclusion set and no-roll skip behavior.

### Risks
1. Over-expanding `_COMMON_DESCRIPTORS` could suppress real NPC names that happen to be descriptors. Keep the list to unambiguous common adjectives and small cardinal numbers only.

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

**What:** Assert that if the narration contains explicit key-use language ("slid the key", "turned the key", "inserted the key", "unlocked" + item name that ends in `_key`) and the pre-turn state contains that key, the post-turn state should NOT contain it at the same amount. Severity: `yellow` (narrative language is ambiguous; hard FAIL would produce too many false positives).

**Code Snippet**
```python
_KEY_USE_PHRASES: tuple[str, ...] = (
    "slid the", "turned the", "inserted the", "used the", "unlocked"
)

def check_key_consumed_after_use(event: dict, prev_event: dict | None, **_) -> dict:
    narration = event.get("narration", "")
    if not any(p in narration.lower() for p in _KEY_USE_PHRASES):
        return {"severity": "yellow", "result": "skip", "reason": "no key-use language"}
    pre = (event.get("state_snapshot_before") or {}).get("inventory", [])
    post = (event.get("state_snapshot") or {}).get("inventory", [])
    pre_keys = {i["id"]: i.get("amount", 1) for i in pre if i["id"].endswith("_key")}
    post_keys = {i["id"]: i.get("amount", 1) for i in post if i["id"].endswith("_key")}
    for kid, pre_amt in pre_keys.items():
        if post_keys.get(kid, 0) >= pre_amt:
            return {
                "severity": "yellow",
                "result": "fail",
                "reason": f"{kid} not removed after apparent key use",
            }
    return {"severity": "yellow", "result": "pass"}
```

**Validation:** Simulate a T8-like event where narration contains "slid the brass key" and pre-state has `brass_key` at amount 1, post-state still has it at amount 1; assert the assert returns `fail`.

---

#### Step 2.2 — Add `check_no_negative_inventory`

**File:** `ccya/eval/universal_asserts.py`

**What:** Assert that no inventory item in `state_snapshot` has `amount < 1`. Severity: `red` (zero or negative amounts are always a bug).

**Code Snippet**
```python
def check_no_negative_inventory(event: dict, prev_event: dict | None, **_) -> dict:
    inventory = (event.get("state_snapshot") or {}).get("inventory", [])
    bad = [i["id"] for i in inventory if i.get("amount", 1) < 1]
    if bad:
        return {"severity": "red", "result": "fail", "reason": f"zero/negative inventory: {bad}"}
    return {"severity": "red", "result": "pass"}
```

**Validation:** Test with state containing `credits` at `amount: 0`; assert `fail`.

---

#### Step 2.3 — Register new asserts in `run_all_universal_asserts`

**File:** `ccya/eval/universal_asserts.py`

**What:** Add both new functions to the list inside `run_all_universal_asserts` so they run on every turn.

**Validation:** `KNOWN_ASSERT_FIELDS` in `engine_mirror.py` must also be updated; confirm `test_eval_schema.py` passes after the update.

---

#### Step 2.4 — Update `KNOWN_ASSERT_FIELDS` in engine_mirror

**File:** `ccya/eval/engine_mirror.py`

**What:** Add `"check_key_consumed_after_use"` and `"check_no_negative_inventory"` to `KNOWN_ASSERT_FIELDS`.

**Validation:** `tests/test_eval_schema.py` schema validation passes.

---

### Tests to write or update
- `tests/test_universal_asserts.py`: unit tests for both new asserts covering pass, fail, and skip paths.
- `tests/test_eval_schema.py`: will pass automatically once `KNOWN_ASSERT_FIELDS` is updated.

### REPOMAP and architecture updates
- `docs/REPOMAP/eval.md` universal_asserts section: add both new assert function entries.

### Risks
1. `check_key_consumed_after_use` relies on `state_snapshot_before` existing in the event. Confirm runner injects `state_snapshot` (pre-delta) before extraction; if not, the assert will always skip.
2. Key IDs that don't end in `_key` will be missed. Broaden the ID pattern only after inspecting pack conventions — avoid over-generalizing.

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

**Code Snippet**
```python
fallback_turns = sum(
    1 for e in events
    if e.get("scope", {}).get("decided_by", "narrator") != "narrator"
)
scope_fallback_rate = fallback_turns / len(events) if events else 0.0
metrics_rows.append(("Scope fallback rate", f"{scope_fallback_rate:.0%}", "-", "-"))
```

**Validation:** Run a trace with a known scope fallback turn; confirm the rate row appears in the metrics table.

---

#### Step 3.2 — Add per-turn momentum to metrics rows

**File:** `ccya/eval/judge.py` (`_build_metrics_rows`)

**What:** If the emitted event contains a `momentum` block (added by system-cohesion Phase 04), add `momentum.after` as a column in the per-turn metrics table.

**Code Snippet**
```python
momentum_after = event.get("momentum", {}).get("after", "—")
row = (...existing cols..., momentum_after)
```

**Validation:** Run a smoke trace; confirm the momentum column appears per turn.

---

### Tests to write or update
- `tests/test_eval.py`: update `build_trace()` test to assert scope fallback rate row is present in Deterministic Signals when applicable.

### REPOMAP and architecture updates
- `docs/REPOMAP/eval.md` judge.py section: document scope fallback rate and momentum column additions.

### Risks
1. `_build_metrics_rows` may have a fixed column structure; adding a column may break report rendering alignment. Test rendering at multiple column counts.

---

## Implementation — Phase 04: Scenario fixture accuracy

### Files to pull for context
- `evals/scenarios/full_cycle.py` (all TurnAssert entries)
- `ccya/eval/engine_mirror.py` (`KNOWN_ASSERT_FIELDS`, `EXTRACT_STREAMS`)
- `ccya/eval/scenario.py` (`TurnAssert`, `Turn`)

### Detailed steps

#### Step 4.1 — Fix T5 scene tag assertion

**File:** `evals/scenarios/full_cycle.py`

**What:** Change the T5 assert that expects `"combat"` in `scene_tags` to expect `"standoff"` or `"tense_confrontation"` instead. Use a flexible check: assert that at least one of the tension tags is present.

**Why:** T5 narration described a verbal standoff with armed toughs, not active combat. The assert was wrong, not the engine.

**Code Snippet**
```python
TurnAssert(
    turn=5,
    path="extraction.scene.output.scene_tags",
    op="contains_any",
    value=["standoff", "tense_confrontation", "intimidation"],
    severity="yellow",
),
```

**Validation:** `tests/test_eval_schema.py` should continue to pass (path is valid). Run the scenario and confirm T5 no longer produces a false FAIL.

---

#### Step 4.2 — Add T3 inventory credit assert

**File:** `evals/scenarios/full_cycle.py`

**What:** Add a TurnAssert at T3 checking that `state_snapshot.inventory` contains `credits` with an amount greater than the pre-turn value (Halden's 100 credit payment).

**Code Snippet**
```python
TurnAssert(
    turn=3,
    path="state_snapshot.inventory[id=credits].amount",
    op="gt",
    value="$prev",  # or numeric floor if seed value is known
    severity="yellow",
),
```

*Note: verify the `op="gt"` with `"$prev"` syntax is supported by `_check_asserts` in runner.py; if not, use a fixed floor based on the seed state's credits value.*

**Validation:** Confirm `_check_asserts` handles the assert path correctly; run scenario and verify no schema error.

---

#### Step 4.3 — Add T8 key removal assert

**File:** `evals/scenarios/full_cycle.py`

**What:** Add a TurnAssert at T8 verifying `brass_key` is absent from `state_snapshot.inventory` after the key-use turn.

**Code Snippet**
```python
TurnAssert(
    turn=8,
    path="state_snapshot.inventory",
    op="not_contains_id",
    value="brass_key",
    severity="yellow",
),
```

*Note: verify `op="not_contains_id"` is a supported operator in `_check_asserts`. If not, use the nearest equivalent or add the operator as a small extension.*

**Validation:** Schema test passes; scenario run produces correct T8 result.

---

### Tests to write or update
- `tests/test_eval_schema.py`: after fixture changes, re-run to confirm all TurnAssert paths are valid.
- No new test files needed — schema validation covers fixture correctness.

### REPOMAP and architecture updates
- `docs/REPOMAP/eval.md` scenario section: note that `full_cycle.py` was updated to correct T5 tag and add T3/T8 inventory assertions.

### Risks
1. If `op="contains_any"` or `op="not_contains_id"` are not implemented in `_check_asserts`, they must be added before the fixture update — that is a runner change, not just a fixture change.
2. T3 credits assert depends on knowing the seed state's credit balance; read the eval-pack seed state before hardcoding a floor value.

---

## Ambiguities requiring resolution before execution

1. Does `runner.py:_check_asserts` support `op="contains_any"` and `op="not_contains_id"`? Options: A) they exist; B) add them as small extensions; C) rewrite as separate per-value asserts.
2. Does each emitted event include a `state_snapshot_before` (pre-delta) key as well as `state_snapshot` (post-delta)? Needed for `check_key_consumed_after_use`. If not, the runner must be updated to inject it before extraction runs.
3. Is the T3 seed state credits balance known? Read `evals/packs/eval-pack/pack.yaml` or equivalent seed before writing the T3 floor value.
