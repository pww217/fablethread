# Eval Rubric and Judge Remediation

## Status
`open`

## Part of
`eval-results-remediation`

## Dependencies
- None. The eval system is fully independent of the engine pipeline. This plan can be executed before, during, or after Plans A–D.

## Objective
The two eval runs revealed that the current judge rubric is under-specified: dimensions lack anchored score definitions, the rubric does not penalize empty `gm_beat.instruction`, cross-turn consistency is not scored, and the post-run synthesis is optional rather than required. The auto-checker also lacks assertions that would have caught the field-routing and pressure lifecycle bugs found in the eval. This plan rewrites the judge rubric, adds anchored score anchors, adds an auto-fail assertion for empty beats, adds a state-snapshot diff output, and makes synthesis mandatory.

## Non-goals
- Does NOT change the eval runner infrastructure (`run_eval.py`, scenario YAML loading, event log format).
- Does NOT change how eval scenarios are authored or how turns are simulated.
- Does NOT change how FakeLLM is used in unit tests — this is the eval judge only.
- Does NOT change the `REPORT.md` template structure, only its rubric content.
- Does NOT implement a new eval dimension for rules accuracy (the rules extractor changes in Plan B affect this indirectly, but the rubric dimension already covers roll classification).

## Affected files
| File | Change type | Summary of change |
|---|---|---|
| `ccya/eval/judge_prompt.j2` (or equivalent) | modify | Full rubric rewrite: 7 weighted dimensions, anchored 1/5/10 score definitions, auto-fail condition |
| `ccya/eval/universal_asserts.py` (or equivalent) | modify | Add assertions: `gm_beat_instruction_not_empty`, `no_duplicate_compendium_ids`, `pressure_not_removed_on_location_change_alone` |
| `ccya/eval/report.py` (or equivalent) | modify | Make cross-run synthesis mandatory; add state-snapshot diff section to report output |
| `docs/REPOMAP/eval.md` | update | Document new rubric dimensions and new assertions |
| `docs/plans/TODO.md` | update | Add this plan |

## Firm decisions

1. **Seven weighted dimensions** replace the current rubric. Weights are approximate and used for scoring guidance, not hard math. The judge still outputs integer scores per dimension; the synthesis uses them qualitatively.
2. **Anchored score definitions** at 1 (failing), 5 (mediocre/present but flawed), and 10 (excellent) for each dimension. These make inter-run score drift detectable.
3. **Auto-fail on empty `gm_beat.instruction`** is a binary flag in the judge output, not a dimension deduction. If `gm_beat` is non-null but `instruction` is empty or null, the judge must flag `beat_quality_fail: true` regardless of other scores.
4. **Cross-run synthesis is mandatory**, not optional. The report generator must error (not warn) if synthesis is absent after a multi-turn run.
5. **State-snapshot diff** is a structured output section: after each turn, the judge compares the declared state delta against the narration and outputs a list of `{field, expected, actual, match: bool}` rows. This makes silent extraction bugs visible in the report.
6. **The rubric prompt is in a Jinja2 template** (not hardcoded). Dimensions, weights, and anchors are all in the template so they can be updated without touching Python.

## Implementation — Phase 1: Judge rubric rewrite

### Context files to load
- `ccya/eval/judge_prompt.j2` (or equivalent — read first to confirm filename)
- `ccya/eval/` directory listing

### Overview
Replace the rubric section of the judge prompt with the seven-dimension weighted rubric. Add score anchors. Add the auto-fail beat condition.

### Detailed steps

#### Step 1.1 — Rewrite judge rubric template

**File:** `ccya/eval/judge_prompt.j2` (confirm filename before editing)

**What:** Replace the rubric section entirely. Keep all other judge prompt structure (output schema, instructions) verbatim.

**Why:** The old rubric had vague dimensions without anchors, causing inconsistent scores across runs and making regression detection unreliable.

**Code Snippet** (rubric section replacement):
```jinja2
## Evaluation rubric

Score each dimension 1–10. Use the anchors. Do not interpolate randomly — anchor to 1, 5, or 10 and adjust by 1–2 points for nuance.

### Dimension 1 — Narration fidelity (weight: high)
Does the extracted state delta faithfully reflect what the narration said? Are all mentioned NPCs, items, locations, and events captured? Are things NOT mentioned in the narration absent from the delta?
- 1: Major omissions or hallucinations — key NPCs or events missing; items extracted that weren't mentioned.
- 5: Mostly correct with 1–2 minor gaps or a single low-stakes hallucination.
- 10: Delta is a precise, complete reflection of the narration. Nothing missing, nothing invented.

### Dimension 2 — Prose and narrative quality (weight: medium)
Is `outcome_summary` vivid and specific? Are `actions` distinct, bold, and grounded in the current scene and quest? Is the narration itself (if being judged) well-written?
- 1: `outcome_summary` is mechanical or empty. Actions are vague, repetitive, or unrelated to the scene.
- 5: `outcome_summary` is adequate but flat. Actions are plausible but generic.
- 10: `outcome_summary` captures the narrative moment with flavor. All 4 actions are distinct, bold, and could each meaningfully advance the story in a different direction.

### Dimension 3 — Rules classification accuracy (weight: high)
Did the rules extractor correctly identify whether a roll was needed? Was the skill correct? Was the band (success/failure tier) correct given the narration outcome?
- 1: Roll required when it shouldn't be (or vice versa). Wrong skill. Band contradicts narration.
- 5: Roll decision correct; minor skill mismatch or band off by one tier.
- 10: Roll decision, skill, and band are all correct and consistent with the narration outcome.

### Dimension 4 — Inventory and condition extraction (weight: high)
Did the state extractor correctly capture all item gains, losses, and condition changes? No phantom items. No missed transfers.
- 1: Items or conditions clearly stated in narration are absent. Items not mentioned are extracted.
- 5: Most items correct; 1 minor miss or 1 borderline ambiguous item extracted.
- 10: Every explicit transfer and condition change is captured. Nothing invented.

### Dimension 5 — Quest and pressure tracking (weight: high)
Are quest objective completions correct? Are pressures added when threats appear and removed only when threats resolve? Are contact/meet objectives handled correctly?
- 1: Objective marked done with no evidence; pressure removed on location change alone; major quest miss.
- 5: Quest mostly correct; 1 pressure lifecycle error or 1 ambiguous objective decision.
- 10: All objective transitions are correct. Pressure lifecycle is clean — add on threat, remove on resolution only.

### Dimension 6 — GM beat quality (weight: medium)
Is the `gm_beat` present when it should be? Is `instruction` concrete, entity-specific, and actionable for the narrator? Is `type` and `surface_as` correct?
- 1: Beat present with empty/generic instruction. Wrong `type`. `null` when a beat was clearly warranted.
- 5: Beat present with a specific instruction but minor `type` or `surface_as` mismatch.
- 10: Beat is well-timed, instruction names a specific entity and gives the narrator a concrete hook, `type` and `surface_as` are correct.

**Auto-fail flag**: If `gm_beat` is non-null but `instruction` is null or empty, set `beat_instruction_fail: true` in output regardless of dimension score.

### Dimension 7 — Cross-turn consistency (weight: medium)
Do NPC notes, quest states, scene pressures, and inventory carry forward correctly from one turn to the next? Does the model remember what happened two turns ago?
- 1: State from a prior turn is ignored or contradicted. NPCs forget prior interactions.
- 5: Mostly consistent; 1–2 minor continuity errors that don't affect gameplay.
- 10: Complete continuity. Prior state informs current extraction correctly throughout the run.

## Output schema

```json
{
  "scores": {
    "narration_fidelity": 0,
    "prose_quality": 0,
    "rules_classification": 0,
    "inventory_condition": 0,
    "quest_pressure": 0,
    "gm_beat_quality": 0,
    "cross_turn_consistency": 0
  },
  "beat_instruction_fail": false,
  "dimension_notes": {
    "narration_fidelity": "",
    "prose_quality": "",
    "rules_classification": "",
    "inventory_condition": "",
    "quest_pressure": "",
    "gm_beat_quality": "",
    "cross_turn_consistency": ""
  },
  "overall_summary": "",
  "critical_failures": []
}
```

`critical_failures`: list of strings. Each is a specific, actionable failure that would affect gameplay — not style notes. Examples: "Objective 2 marked done with no roll success and no explicit narrative resolution.", "Pressure 'guards_hunting' removed on location change — no narrative evidence threat resolved."
```

**Validation:** Template renders without Jinja error. Parse the output schema against `JudgeOutput` model (if one exists) — confirm all keys match.

---

## Implementation — Phase 2: Auto-checker assertions

### Context files to load
- `ccya/eval/universal_asserts.py` (confirm filename — read first)

### Overview
Add three new assertion functions. Each takes a `turn_result` dict and a `state` dict and returns a list of `AssertionFailure` (or equivalent) objects.

### Detailed steps

#### Step 2.1 — Add `assert_gm_beat_instruction_present`

**File:** `ccya/eval/universal_asserts.py`

**What:** Assert that if `gm_beat` is non-null in the `StateDelta` (or `TurnResult`), its `instruction` field is non-empty.

**Code Snippet**
```python
def assert_gm_beat_instruction_present(
    turn_result: dict[str, Any],
    state: dict[str, Any],
    *,
    turn_no: int,
) -> list[AssertionFailure]:
    failures: list[AssertionFailure] = []
    beat = (turn_result.get("delta") or {}).get("gm_beat")
    if beat is not None:
        instruction = (beat.get("instruction") or "").strip()
        if not instruction:
            failures.append(AssertionFailure(
                turn=turn_no,
                assertion="gm_beat_instruction_present",
                detail=f"gm_beat is non-null but instruction is empty. type={beat.get('type')}",
            ))
    return failures
```

**Validation:**
```python
result = assert_gm_beat_instruction_present(
    {"delta": {"gm_beat": {"type": "complication", "instruction": ""}}},
    {},
    turn_no=1,
)
assert len(result) == 1

result2 = assert_gm_beat_instruction_present(
    {"delta": {"gm_beat": None}},
    {},
    turn_no=1,
)
assert len(result2) == 0
```

---

#### Step 2.2 — Add `assert_no_duplicate_compendium_ids`

**File:** `ccya/eval/universal_asserts.py`

**What:** After applying a turn's delta, assert that `state["known_characters"]` contains no duplicate IDs.

**Code Snippet**
```python
def assert_no_duplicate_compendium_ids(
    turn_result: dict[str, Any],
    state: dict[str, Any],
    *,
    turn_no: int,
) -> list[AssertionFailure]:
    failures: list[AssertionFailure] = []
    known = state.get("known_characters") or []
    ids = [npc.get("id") for npc in known if npc.get("id")]
    seen: set[str] = set()
    dupes: list[str] = []
    for npc_id in ids:
        if npc_id in seen:
            dupes.append(npc_id)
        seen.add(npc_id)
    if dupes:
        failures.append(AssertionFailure(
            turn=turn_no,
            assertion="no_duplicate_compendium_ids",
            detail=f"Duplicate NPC IDs in compendium: {dupes}",
        ))
    return failures
```

**Validation:**
```python
state = {"known_characters": [
    {"id": "kael_marsh", "name": "Kael Marsh"},
    {"id": "kael_marsh", "name": "Kael Marsh (duplicate)"},
]}
result = assert_no_duplicate_compendium_ids({}, state, turn_no=2)
assert len(result) == 1
```

---

#### Step 2.3 — Add `assert_pressure_not_removed_on_location_change`

**File:** `ccya/eval/universal_asserts.py`

**What:** If the turn's `delta` has a `location_change` and also has `scene_pressure_remove` entries, check whether each removed pressure had `urgency` of `immediate` or `building`. If so, flag it — unless the `outcome_summary` contains resolution language.

**Why:** The pressure-on-location-change bug is subtle and not caught by model validators. This assertion makes it visible in eval reports.

**Code Snippet**
```python
_RESOLUTION_VERBS: frozenset[str] = frozenset({
    "extinguished", "defused", "evaded", "escaped", "sealed",
    "defeated", "resolved", "neutralized", "locked out",
})

def assert_pressure_not_removed_on_location_change(
    turn_result: dict[str, Any],
    state: dict[str, Any],
    *,
    turn_no: int,
    prior_pressures: list[dict[str, Any]] | None = None,
) -> list[AssertionFailure]:
    failures: list[AssertionFailure] = []
    delta = turn_result.get("delta") or {}
    if not delta.get("location_change"):
        return failures
    removed_ids = delta.get("scene_pressure_remove") or []
    if not removed_ids:
        return failures
    prior = {p["id"]: p for p in (prior_pressures or [])}
    outcome = (turn_result.get("outcome_summary") or "").lower()
    has_resolution = any(verb in outcome for verb in _RESOLUTION_VERBS)
    for pid in removed_ids:
        p = prior.get(pid)
        if p and p.get("urgency") in ("immediate", "building") and not has_resolution:
            failures.append(AssertionFailure(
                turn=turn_no,
                assertion="pressure_not_removed_on_location_change",
                detail=(
                    f"Pressure '{pid}' (urgency={p.get('urgency')}) removed on location change "
                    f"with no resolution language in outcome_summary."
                ),
            ))
    return failures
```

**Validation:**
```python
prior = [{"id": "guards_hunting", "urgency": "immediate", "text": "Guards on alert"}]
delta = {"location_change": {"id": "market"}, "scene_pressure_remove": ["guards_hunting"]}
result = assert_pressure_not_removed_on_location_change(
    {"delta": delta, "outcome_summary": "You walk briskly to the market."},
    {},
    turn_no=3,
    prior_pressures=prior,
)
assert len(result) == 1
```

---

## Implementation — Phase 3: Mandatory synthesis and state diff

### Context files to load
- `ccya/eval/report.py` (or equivalent — confirm filename)

### Overview
Two changes: (1) enforce synthesis presence at report generation time; (2) add a state-snapshot diff section that surfaces extraction mismatches.

### Detailed steps

#### Step 3.1 — Enforce mandatory synthesis in `report.py`

**File:** `ccya/eval/report.py`

**What:** In the report generation function, add a guard: if the run has more than 1 turn and `synthesis` is absent or empty in the judge output, raise `ValueError` (not a warning). Log the specific run ID.

**Why:** Synthesis was optional and routinely skipped, making cross-run regression invisible.

**Code Snippet**
```python
def _validate_synthesis_present(
    judge_outputs: list[dict[str, Any]],
    run_id: str,
    turn_count: int,
) -> None:
    if turn_count <= 1:
        return
    for output in judge_outputs:
        synthesis = (output.get("overall_summary") or "").strip()
        if not synthesis:
            raise ValueError(
                f"Eval run '{run_id}': overall_summary (synthesis) is required for "
                f"multi-turn runs but was absent or empty. Populate this field before "
                f"finalizing the report."
            )
```

**Validation:** Call `_validate_synthesis_present` with an empty `overall_summary` — assert `ValueError` is raised. Call with a non-empty summary — assert no error.

---

#### Step 3.2 — Add state-snapshot diff to report output

**File:** `ccya/eval/report.py`

**What:** After each turn's judge output is processed, compute a structured diff between `turn_result.delta` and the narration. Output as a list of `{field, expected, actual, match}` rows appended to the REPORT.md under a `## State Snapshot Diff` section.

The diff is heuristic, not exhaustive. Check these fields only:
- `inventory_add`: each item ID should appear (or be reasonably inferable) in the narration string.
- `scene_pressure_add`: each pressure ID should correspond to a threat described in narration.
- `compendium_npc_update`: each NPC ID updated should appear in the narration or be a known alias.
- `gm_beat.instruction`: should not be empty if beat is non-null.

**Code Snippet**
```python
def _compute_state_diff(
    delta: dict[str, Any],
    narration: str,
    turn_no: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    lower_narration = narration.lower()

    for item in (delta.get("inventory_add") or []):
        name = (item.get("name") or item.get("id") or "").lower()
        match = name in lower_narration
        if not match:
            rows.append({
                "turn": turn_no,
                "field": "inventory_add",
                "expected": f"'{name}' mentioned in narration",
                "actual": "not found in narration text",
                "match": False,
            })

    for p in (delta.get("scene_pressure_add") or []):
        # Minimal check: urgency is set
        if not p.get("urgency"):
            rows.append({
                "turn": turn_no,
                "field": "scene_pressure_add",
                "expected": "urgency set",
                "actual": "urgency missing",
                "match": False,
            })

    beat = delta.get("gm_beat")
    if beat is not None:
        instruction = (beat.get("instruction") or "").strip()
        rows.append({
            "turn": turn_no,
            "field": "gm_beat.instruction",
            "expected": "non-empty",
            "actual": instruction or "(empty)",
            "match": bool(instruction),
        })

    return rows
```

**Validation:** Run against a known eval turn result where `inventory_add` contains "envelope" and the narration says "she hands you an envelope" — assert no diff rows for that item. Run with `inventory_add` containing "sword" and no mention of sword in narration — assert one diff row.

---

### Tests to write or update

**File:** `tests/test_eval_asserts.py` (create)
```python
def test_assert_gm_beat_instruction_present_fails_on_empty():
    ...

def test_assert_gm_beat_instruction_present_passes_on_null_beat():
    ...

def test_assert_no_duplicate_compendium_ids_catches_dupe():
    ...

def test_assert_no_duplicate_compendium_ids_passes_clean_state():
    ...

def test_assert_pressure_not_removed_on_location_change_fires():
    ...

def test_assert_pressure_not_removed_on_location_change_clean():
    ...

def test_mandatory_synthesis_raises_on_empty():
    from ccya.eval.report import _validate_synthesis_present
    import pytest
    with pytest.raises(ValueError):
        _validate_synthesis_present([{"overall_summary": ""}], "run_001", turn_count=3)

def test_mandatory_synthesis_passes_on_present():
    from ccya.eval.report import _validate_synthesis_present
    _validate_synthesis_present([{"overall_summary": "The run showed consistent NPC tracking."}], "run_001", turn_count=3)
```

### REPOMAP updates required
`docs/REPOMAP/eval.md` — document all 7 rubric dimensions with weights; document the 3 new assertions; document mandatory synthesis enforcement; document state-snapshot diff output.

### Risks
1. **Judge output schema change** — existing eval run REPORT.md files used the old schema. New runs will have a different output structure. The report generator must handle both (check for old keys, default to empty if absent). Do not break report generation for archived runs.
2. **`assert_pressure_not_removed_on_location_change` requires `prior_pressures`** — the caller must pass the pressure list from before the delta was applied, not after. The eval runner must snapshot pressure state before applying each turn's delta. Read the eval runner to confirm this is feasible before implementing.
3. **State-snapshot diff false positives** — item name matching against raw narration text is fragile (plurals, pronouns, paraphrasing). The diff is advisory, not a hard assertion. Mark all diff rows with `advisory: true` if that distinction is useful in the report.
4. **Judge prompt template file location** — read `ccya/eval/` directory first. The file may be `judge_prompt.j2`, `judge_system.j2`, or embedded in `report.py`. Confirm before editing.

## Ambiguities requiring resolution before execution
None.

## TODO.md update
Under `## P1 — Active`:
Eval rubric and judge remediation — docs/plans/eval-results-remediation/eval-results-remediation-eval-rubric.md