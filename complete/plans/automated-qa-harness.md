# Automated QA Harness

## Status
`completed`

## Objective
The eval pipeline currently produces a judge report that is scored by an LLM. The LLM judge is valuable for qualitative dimensions but cannot reliably catch mechanical failures that are deterministic. Nine mechanical failure classes are currently detectable from `events.jsonl` alone without any LLM call: zero-stack overdraw, pressure count exceeding caps, consecutive floor momentum without relief, directive rendering failures, quest ID collision (already asserted), immediate pressure age violations, momentum delta violations (already asserted), NPC scene cap violations (already asserted), and compaction sanitization failures (already asserted). Of these, only 4 are currently asserted. The remaining 5 need new assert functions. Beyond adding asserts, the harness needs: a `--gate` mode that fails the run if any RED assert fires (enabling CI integration), a per-assert failure summary table in the report, and a pacing metrics section that computes pressure durations, consecutive floor counts, and location-turn dwell across a full run. Currently none of this is automated — it requires manual rubric scoring by the judge.

## Non-goals
- Does not replace the LLM judge — qualitative dimensions (narrative coherence, directive tone, quest arc) still require judge scoring.
- Does not add a web UI or dashboard — CLI only.
- Does not change how events are written by the game engine.
- Does not modify existing assert signatures — only adds new ones and wires them into `run_all_universal_asserts`.
- Does not add new Pydantic models.

## Firm decisions

1. **Gate mode is opt-in, default off.** `--gate` causes a non-zero exit code if any assert with `severity="red"` fails. Default behavior (no `--gate`) continues to produce the report without failing. CI pipelines use `--gate`; human review runs do not.
2. **Assert severity levels: `red` (mechanical bug, always wrong), `yellow` (quality issue, context-dependent).** The 12 existing asserts are all `red` (they catch bugs, not style). New asserts inherit the appropriate level.
3. **Pacing metrics are computed, not judged.** Pressure duration (turns active), consecutive floor turns, location dwell (turns in same location), condition duration — all are computed directly from `state_snapshot` fields across events. These appear as a metrics table in the report, not as scored dimensions.
4. **Assert results in report are a table, not prose.** Format: `| assertion | turns_failed | turns_checked | first_failure |`. The judge's existing scored dimensions remain separate from this table.
5. **New asserts follow existing signature:** `check_xxx(event, prev_event) -> dict` with keys `assertion`, `passed`, `detail`, `scope`. Severity is added as a new key `severity: "red" | "yellow"`.

## Implementation — Phase 1: New Assert Functions

### Context files to load
- `ccya/eval/universal_asserts.py`
- `ccya/models.py` (for field names)

### Overview
Add five new assert functions. Each addresses one uncovered mechanical failure class.

### Detailed steps

#### Step 1.1 — check_zero_stack_overdraw

**File:** `ccya/eval/universal_asserts.py`

**What:** Check whether `applied.inventory_remove` contains a remove delta for an item that was at amount 0 in the prior turn's state snapshot.

```python
def check_zero_stack_overdraw(
    event: dict[str, Any], prev_event: dict[str, Any] | None
) -> dict[str, Any]:
    """inventory_remove must not remove from a zero-quantity item."""
    if prev_event is None:
        return {"assertion": "universal.inventory.no_overdraw", "passed": True, "detail": "(first turn)", "scope": "universal", "severity": "red"}
    prev_inv = (prev_event.get("state_snapshot") or {}).get("inventory") or []
    zero_items = {
        item["id"] for item in prev_inv
        if isinstance(item, dict) and (item.get("amount") or 0) == 0 and item.get("id")
    }
    removes = (event.get("applied") or {}).get("inventory_remove") or []
    bad = [r for r in removes if isinstance(r, dict) and r.get("id") in zero_items]
    if bad:
        return {
            "assertion": "universal.inventory.no_overdraw",
            "passed": False,
            "detail": f"removed from zero-quantity item(s): {[b.get('id') for b in bad]}",
            "scope": "universal",
            "severity": "red",
        }
    return {"assertion": "universal.inventory.no_overdraw", "passed": True, "detail": f"checked {len(removes)} removes", "scope": "universal", "severity": "red"}
```

**Validation:** Test fixture: prev_event has item `credits` at amount 0; event has `applied.inventory_remove = [{"id": "credits", "amount": 5}]`. Assert fires.

***

#### Step 1.2 — check_immediate_pressure_cap

**File:** `ccya/eval/universal_asserts.py`

**What:** The count of `immediate` urgency pressures in `state_snapshot.scene.scene_pressure` must not exceed 3 at any point.

```python
def check_immediate_pressure_cap(event: dict[str, Any], prev_event: dict[str, Any] | None = None) -> dict[str, Any]:
    """Immediate pressures must not exceed 3 at once."""
    pressures = ((event.get("state_snapshot") or {}).get("scene") or {}).get("scene_pressure") or []
    immediates = [p for p in pressures if isinstance(p, dict) and p.get("urgency") == "immediate"]
    if len(immediates) > 3:
        ids = [p.get("id", "?") for p in immediates]
        return {"assertion": "universal.pressure.immediate_cap", "passed": False, "detail": f"{len(immediates)} immediate pressures (cap 3): {ids}", "scope": "universal", "severity": "red"}
    return {"assertion": "universal.pressure.immediate_cap", "passed": True, "detail": f"{len(immediates)} immediate", "scope": "universal", "severity": "red"}
```

**Validation:** Fixture with 4 immediate pressures → assert fires.

***

#### Step 1.3 — check_momentum_floor_no_relief

**File:** `ccya/eval/universal_asserts.py`

**What:** If momentum has been at floor (-3) for ≥ 3 consecutive turns (as seen in the event + prev_event chain), flag as yellow. This assert requires access to a small window of prior events, which `run_all_universal_asserts` doesn't currently provide. Solution: add an optional `event_window: list[dict] | None` parameter to this specific assert, and pass the last 3 events from the runner.

```python
def check_momentum_floor_no_relief(
    event: dict[str, Any],
    prev_event: dict[str, Any] | None,
    event_window: list[dict] | None = None,
) -> dict[str, Any]:
    """Momentum at floor for >= 3 consecutive turns without a success band is a pacing failure."""
    window = event_window or ([prev_event, event] if prev_event else [event])
    floor_count = 0
    for ev in reversed(window):
        m = ((ev.get("state_snapshot") or {}).get("meta") or {}).get("momentum")
        if m is not None and m <= -3:
            floor_count += 1
        else:
            break
    if floor_count >= 3:
        return {"assertion": "universal.pacing.floor_no_relief", "passed": False, "detail": f"momentum at floor for {floor_count} consecutive turns", "scope": "universal", "severity": "yellow"}
    return {"assertion": "universal.pacing.floor_no_relief", "passed": True, "detail": f"floor_count={floor_count}", "scope": "universal", "severity": "yellow"}
```

**Validation:** Window of 3 events all at momentum=-3 → assert fires as yellow.

***

#### Step 1.4 — check_directive_rendered

**File:** `ccya/eval/universal_asserts.py`

**What:** If `state_snapshot.scene.scene_pressure` contains any `immediate` entry, the narrate rendered user prompt must contain the string `**Pressure:**` or `**Overwhelm:**`. This catches the `scene_pressure` wiring bug deterministically.

```python
def check_directive_rendered(event: dict[str, Any], prev_event: dict[str, Any] | None = None) -> dict[str, Any]:
    """If immediate pressures exist, the Pressure/Overwhelm directive must appear in narrate user prompt."""
    pressures = ((event.get("state_snapshot") or {}).get("scene") or {}).get("scene_pressure") or []
    immediates = [p for p in pressures if isinstance(p, dict) and p.get("urgency") == "immediate"]
    if not immediates:
        return {"assertion": "universal.narrate.pressure_directive_rendered", "passed": True, "detail": "(no immediates)", "scope": "universal", "severity": "red"}
    rendered = (event.get("narrate_prompt") or {}).get("rendered_user") or ""
    if "**Pressure:**" in rendered or "**Overwhelm:**" in rendered:
        return {"assertion": "universal.narrate.pressure_directive_rendered", "passed": True, "detail": "directive present", "scope": "universal", "severity": "red"}
    return {"assertion": "universal.narrate.pressure_directive_rendered", "passed": False, "detail": f"{len(immediates)} immediate pressures but no Pressure/Overwhelm directive in narrate user prompt", "scope": "universal", "severity": "red"}
```

**Validation:** Event with 1 immediate pressure and `rendered_user` lacking `**Pressure:**` → assert fires.

***

#### Step 1.5 — check_immediate_pressure_stale

**File:** `ccya/eval/universal_asserts.py`

**What:** If an `immediate` pressure has `turn_became_immediate` set and the current turn exceeds `turn_became_immediate + 8`, flag as yellow (it should have expired).

```python
def check_immediate_pressure_stale(event: dict[str, Any], prev_event: dict[str, Any] | None = None) -> dict[str, Any]:
    """Immediate pressures older than 8 turns since becoming immediate are stale."""
    cur_turn = int((event.get("state_snapshot") or {}).get("meta", {}).get("turn") or 0)
    pressures = ((event.get("state_snapshot") or {}).get("scene") or {}).get("scene_pressure") or []
    stale = []
    for p in pressures:
        if not isinstance(p, dict) or p.get("urgency") != "immediate":
            continue
        tbi = p.get("turn_became_immediate")
        if tbi and (cur_turn - tbi) > 8:
            stale.append(p.get("id", "?"))
    if stale:
        return {"assertion": "universal.pressure.no_stale_immediate", "passed": False, "detail": f"stale immediate pressure(s): {stale}", "scope": "universal", "severity": "yellow"}
    return {"assertion": "universal.pressure.no_stale_immediate", "passed": True, "detail": "no stale immediates", "scope": "universal", "severity": "yellow"}
```

`turn_became_immediate` is populated by `ccya/engine/pressure.py` when pressures escalate to `immediate` urgency (set at `turn_became_immediate = current_turn` with TTL of 8 turns). This assert will fire on real traces where stale immediate pressures exist.

**Validation:** Fixture with immediate pressure at `turn_became_immediate=1`, current_turn=12 → assert fires.

***

#### Step 1.6 — Wire all 5 new asserts into run_all_universal_asserts

**File:** `ccya/eval/universal_asserts.py`

**What:** Add all five to the `results` list in `run_all_universal_asserts`. For `check_momentum_floor_no_relief`, pass `event_window=None` (runner will pass the window separately in Phase 2).

**Code Snippet:**
```python
def run_all_universal_asserts(
    event: dict[str, Any], prev_event: dict[str, Any] | None, event_window: list[dict] | None = None
) -> list[dict[str, Any]]:
    results = [
        # ... existing 10 asserts ...
        check_zero_stack_overdraw(event, prev_event),
        check_immediate_pressure_cap(event),
        check_directive_rendered(event),
        check_immediate_pressure_stale(event),
        check_momentum_floor_no_relief(event, prev_event, event_window=event_window),
    ]
    results.extend(_assert_quest_id_collision(event, prev_event))
    results.extend(_assert_compactor_sanitization_nonzero(event, prev_event))
    return results
```

**Validation:** All 5 new asserts appear in output of `run_all_universal_asserts` with a clean fixture.

***

## Implementation — Phase 2: Gate Mode in runner.py and cli.py

### Context files to load
- `ccya/eval/runner.py`
- `ccya/eval/cli.py`

### Overview
Add `--gate` CLI flag. After replaying all events, if any `severity="red"` assert failed, print a summary to stderr and exit with code 1.

### Detailed steps

#### Step 2.1 — Add --gate flag to cli.py

**File:** `ccya/eval/cli.py`

**What:** Add `--gate` flag with default off. Pass it through to the runner. The CLI uses `argparse` (not click).

**Code Snippet:**
```python
run.add_argument("--gate", action="store_true", help="Exit 1 if any red assert fails.")
```

**Validation:** `python -m ccya.eval run --help` shows `--gate`.

***

#### Step 2.2 — Accumulate assert failures in runner.py and apply gate

**File:** `ccya/eval/runner.py`

**What:**
- In the event replay loop, collect all assert results into `all_assert_results: list[dict]`.
- Pass `event_window` (last 3 events) to `run_all_universal_asserts`.
- After the loop, if `gate=True`: filter for `passed=False AND severity="red"`. If any exist, print each to stderr and call `sys.exit(1)`.
- Add `import sys` to runner.py (not currently imported).

**Code Snippet:**
```python
all_assert_results: list[dict] = []
event_window: list[dict] = []

for i, event in enumerate(events):
    prev = events[i - 1] if i > 0 else None
    window = events[max(0, i-2):i+1]  # last 3 events including current
    asserts = run_all_universal_asserts(event, prev, event_window=window)
    all_assert_results.extend(asserts)
    event_window = window

if gate:
    red_failures = [r for r in all_assert_results if not r.get("passed") and r.get("severity") == "red"]
    if red_failures:
        for f in red_failures:
            print(f"GATE FAIL [{f['assertion']}]: {f['detail']}", file=sys.stderr)
        sys.exit(1)
```

**Validation:** Run with a fixture that has a zero-stack overdraw. `--gate` mode exits 1. `--no-gate` produces the report normally.

***

## Implementation — Phase 3: Assert Table and Pacing Metrics in report.py

### Context files to load
- `ccya/eval/report.py`

### Overview
Add two new sections to the generated report: (1) an assert summary table showing which asserts failed and on which turns; (2) a pacing metrics section with computed values for pressure duration, location dwell, momentum floor runs, and condition duration.

### Detailed steps

#### Step 3.1 — Add assert summary table

**File:** `ccya/eval/report.py`

**What:** After the existing per-turn sections, add a `## Universal Assert Results` section. Build a table:

```markdown
## Universal Assert Results

| Assertion | Severity | Turns Failed | Turns Checked | First Failure Turn |
|---|---|---|---|---|
| universal.inventory.no_overdraw | 🔴 | 2 | 12 | T6 |
| universal.pressure.immediate_cap | 🔴 | 0 | 12 | — |
| universal.pacing.floor_no_relief | 🟡 | 1 | 12 | T9 |
```

Only assertions that fired at least once are shown in detail. Passing-only assertions get a single `✅ all pass` row.

**Why:** This replaces the manual rubric scoring of these dimensions — they are now computed, not judged.

**Validation:** Run on a known-failure fixture. Confirm the table appears in the report with correct failure counts.

***

#### Step 3.2 — Add pacing metrics section

**File:** `ccya/eval/report.py`

**What:** Compute and render the following from `state_snapshot` fields across all events:

- **Pressure duration table:** for each unique pressure ID seen across events, compute `turns_active = last_turn_seen - first_turn_seen`. Flag any pressure active > 8 turns.
- **Location dwell table:** for each location ID, compute consecutive turns spent there. Flag any dwell > 4 turns.
- **Momentum floor runs:** count runs of consecutive turns at momentum=-3, with turn ranges.
- **Condition duration:** for each condition ID, compute turns active. Flag conditions active > 6 turns with no status change.

Format as markdown tables. No LLM call needed — all computed directly from `state_snapshot` diffs.

**Code Snippet (structure only):**
```python
def _compute_pacing_metrics(events: list[dict]) -> str:
    """Compute pacing metrics from events. Returns markdown string."""
    # pressure durations
    # location dwell
    # momentum floor runs
    # condition durations
    ...
    return markdown_output
```

**Validation:** Run on the full May 11 trace. Confirm pressure duration table shows the T3-T14 combat pressure with duration=11 (should flag). Confirm location dwell shows any overly-long dwells.

***

### Tests to write or update
- `tests/test_universal_asserts.py`: one test per new assert function covering the fail case and the pass case (10 new tests total).
- `tests/test_eval_runner.py` (create if not exists): `test_gate_mode_exits_1_on_red_failure` — mock a red assert failure, run with `gate=True`, assert `SystemExit(1)`.
- `tests/test_eval_runner.py`: `test_gate_mode_passes_on_no_red` — no red failures, `gate=True`, assert exits 0.
- `tests/test_eval_report.py` (create if not exists): `test_assert_table_in_report` — run report generation with known assert results, assert `## Universal Assert Results` heading in output.
- `tests/test_eval_report.py`: `test_pacing_metrics_in_report` — run `_compute_pacing_metrics` with a fixture, assert pressure duration table present.

### REPOMAP updates required
- `docs/REPOMAP/eval.md`: Add all 5 new assert functions with signatures and descriptions.
- `docs/REPOMAP/eval.md`: Document `--gate` mode in `cli.py` and `runner.py`.
- `docs/REPOMAP/eval.md`: Document `_compute_pacing_metrics` in `report.py`.
- `docs/REPOMAP/eval.md`: Update `run_all_universal_asserts` signature to include `event_window` param.

### Risks
1. **`event_window` signature change breaks existing callers of `run_all_universal_asserts`** — the runner calls it. Adding `event_window=None` as an optional kwarg is backward-compatible. Existing callers pass positional args `(ev, prev_ev)` which remain valid.
2. **Pacing metrics computation is O(n²) for large traces** — pressure duration requires scanning all events for each pressure ID. With 12-turn traces this is trivial; with 100-turn traces it could be slow. Mitigation: use a dict keyed by pressure ID to accumulate first/last seen in a single O(n) pass.
3. **`severity` key not present on existing asserts** — the gate filter checks `severity == "red"`. Existing asserts don't have this key. Mitigation: filter as `r.get("severity", "red") == "red"` to default missing severity to red (conservative). OR add `"severity": "red"` to all existing assert return dicts (cleaner). Executor should choose and be consistent.
4. **Report generation receives pre-computed results from runner, not re-runs asserts.** `report.py` receives `RunResult` and renders via `_render_auto_checker_block()` which iterates `turn.assert_results`. No `event_window` change needed in report.py.
